"""
ChatGPT conversation export adapter.

Parses the JSON file produced by OpenAI's "Export data" feature and
converts it into the provider-agnostic ParsedConversation / ParsedMessage
dataclasses used by the ImportPipeline.

ChatGPT export format (conversations.json):
    A JSON array where each element is a conversation object:
    {
        "title": "...",
        "create_time": 1234567890.123,   # Unix timestamp (float)
        "update_time": 1234567891.456,
        "mapping": {                      # All message nodes
            "<node-uuid>": {
                "id": "<node-uuid>",
                "message": {             # null for root-only nodes
                    "id": "<node-uuid>",
                    "author": {"role": "user"|"assistant"|"system"|"tool"},
                    "content": {
                        "content_type": "text",
                        "parts": ["..."]
                    },
                    "create_time": 1234567890.5,
                    "metadata": {"model_slug": "gpt-4", ...}
                },
                "parent": "<parent-uuid>" | null,
                "children": ["<child-uuid>", ...]
            }
        }
    }

Tree structure notes:
    The mapping forms a tree where each conversation can branch (when a
    user edits a message and regenerates). The "canonical" conversation
    path is reconstructed by traversing from the root to the last leaf,
    always following the final child at each branch point (i.e. the most
    recently generated response).

Security notes:
    - Files larger than 100 MB are rejected.
    - eval()/exec() are never used.
    - Only message counts (not content) are logged.
    - All content is returned as plain strings; encryption happens in the
      ImportPipeline.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from vault.ingestion.base import BaseAdapter, ParsedConversation, ParsedMessage

logger = logging.getLogger(__name__)

# Maximum file size accepted (bytes)
_MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# ChatGPT author roles mapped to our canonical actor names
_ROLE_MAP: Dict[str, str] = {
    "user": "user",
    "assistant": "assistant",
    "system": "system",
    "tool": "system",       # tool calls treated as system messages
}


class ChatGPTAdapter(BaseAdapter):
    """Ingestion adapter for OpenAI ChatGPT conversation exports.

    Parses the conversations.json file from a ChatGPT data export and
    returns a list of ParsedConversation objects ready for the pipeline.

    Usage::

        adapter = ChatGPTAdapter()
        if adapter.validate_format(Path("conversations.json")):
            convs = adapter.parse(Path("conversations.json"))
            print(f"Parsed {len(convs)} conversations")
    """

    @property
    def provider_name(self) -> str:
        return "chatgpt"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_format(self, file_path: Path) -> bool:
        """Return True if the file looks like a ChatGPT export.

        Performs lightweight checks without loading the full file:
        - File must exist and have a .json extension
        - File must be <= 100 MB
        - Top-level structure must be a non-empty JSON array
        - First element must contain a 'mapping' key

        Args:
            file_path: Path to the candidate export file.

        Returns:
            True if the file appears to be a valid ChatGPT export.
        """
        if not file_path.exists() or file_path.suffix.lower() != ".json":
            return False

        if file_path.stat().st_size > _MAX_FILE_SIZE:
            logger.warning(
                "File %s exceeds 100 MB limit (%d bytes) — rejected",
                file_path,
                file_path.stat().st_size,
            )
            return False

        try:
            with file_path.open("r", encoding="utf-8") as fh:
                # Read only the first 4 KB for quick structure check
                sample = fh.read(4096)

            # Must start with a JSON array
            stripped = sample.lstrip()
            if not stripped.startswith("["):
                return False

            # Attempt a full parse for the structural check
            data = json.loads(file_path.read_text(encoding="utf-8"))
            if not isinstance(data, list) or len(data) == 0:
                return False
            if not isinstance(data[0], dict) or "mapping" not in data[0]:
                return False

            return True

        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return False

    def parse(self, file_path: Path) -> List[ParsedConversation]:
        """Parse a ChatGPT export file into ParsedConversation objects.

        Args:
            file_path: Path to a validated conversations.json file.

        Returns:
            List of ParsedConversation objects (may be empty if all
            conversations have no usable messages).

        Raises:
            ValueError: If the file is malformed or fails schema checks.
            OSError: If the file cannot be read.
        """
        if file_path.stat().st_size > _MAX_FILE_SIZE:
            raise ValueError(
                f"File {file_path} is too large "
                f"(>{_MAX_FILE_SIZE // (1024 * 1024)} MB)."
            )

        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"Failed to parse JSON from {file_path}: {exc}") from exc

        if not isinstance(raw, list):
            raise ValueError(
                f"{file_path} does not contain a top-level JSON array."
            )

        conversations: List[ParsedConversation] = []
        for idx, raw_conv in enumerate(raw):
            if not isinstance(raw_conv, dict):
                logger.debug("Skipping non-dict element at index %d", idx)
                continue
            try:
                conv = self._parse_conversation(raw_conv)
            except Exception as exc:
                logger.warning(
                    "Skipping conversation at index %d due to error: %s",
                    idx,
                    exc,
                )
                continue

            if conv is None:
                continue
            conversations.append(conv)

        logger.info(
            "Parsed %d conversations from %s",
            len(conversations),
            file_path.name,
        )
        return conversations

    # ------------------------------------------------------------------
    # Internal parsing helpers
    # ------------------------------------------------------------------

    def _parse_conversation(
        self, raw: Dict[str, Any]
    ) -> Optional[ParsedConversation]:
        """Parse a single conversation dict from the export array.

        Args:
            raw: Raw conversation dict from the JSON array.

        Returns:
            ParsedConversation, or None if the conversation has no messages.
        """
        external_id: str = raw.get("id") or raw.get("conversation_id") or ""
        title: str = raw.get("title") or "Untitled"
        mapping: Dict[str, Any] = raw.get("mapping") or {}

        create_ts: float = raw.get("create_time") or 0.0
        update_ts: float = raw.get("update_time") or create_ts

        created_at = _ts_to_dt(create_ts)
        updated_at = _ts_to_dt(update_ts)

        # Flatten the tree to an ordered list of message nodes
        message_nodes = self._flatten_message_tree(mapping)

        if not message_nodes:
            return None

        # Build ParsedMessage list and collect metadata
        messages: List[ParsedMessage] = []
        model_slugs: List[str] = []

        for node_msg in message_nodes:
            parsed_msg = self._parse_message(node_msg)
            if parsed_msg is None:
                continue
            messages.append(parsed_msg)
            slug = node_msg.get("metadata", {}).get("model_slug")
            if slug and slug not in model_slugs:
                model_slugs.append(slug)

        if not messages:
            return None

        # Extract conversation-level metadata
        metadata: Dict[str, Any] = {}
        if model_slugs:
            metadata["models"] = model_slugs

        # Generate a stable content hash for deduplication
        content_hash = self._compute_hash(external_id, messages)

        return ParsedConversation(
            external_id=external_id,
            title=title,
            created_at=created_at,
            updated_at=updated_at,
            messages=messages,
            metadata=metadata,
            content_hash=content_hash,
        )

    def _flatten_message_tree(
        self, mapping: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Traverse the mapping tree and return messages in chronological order.

        The mapping is a dict of nodes that form a tree. We find the root
        (the node whose parent is absent from the mapping), then follow
        children depth-first, always taking the last child at branch points
        (corresponding to the most recently generated response in ChatGPT).

        Args:
            mapping: The raw 'mapping' dict from a ChatGPT conversation.

        Returns:
            Ordered list of raw message dicts (nodes that have a non-null
            'message' with parseable content).
        """
        if not mapping:
            return []

        # Find the root: a node whose parent is None or not in mapping
        root_id: Optional[str] = None
        for node_id, node in mapping.items():
            parent = node.get("parent")
            if parent is None or parent not in mapping:
                root_id = node_id
                break

        if root_id is None:
            return []

        # Walk the tree following the last child at each branch
        messages: List[Dict[str, Any]] = []
        current_id: Optional[str] = root_id

        while current_id:
            node = mapping.get(current_id)
            if node is None:
                break

            raw_msg = node.get("message")
            if raw_msg is not None:
                messages.append(raw_msg)

            children: List[str] = node.get("children") or []
            if not children:
                break

            # Follow the last child (most recent branch / regeneration)
            current_id = children[-1]

        return messages

    def _parse_message(
        self, raw_msg: Dict[str, Any]
    ) -> Optional[ParsedMessage]:
        """Parse a single message node into a ParsedMessage.

        Args:
            raw_msg: Raw message dict from a mapping node.

        Returns:
            ParsedMessage, or None if the message should be skipped
            (null content, empty parts, unsupported content type, etc.).
        """
        if not raw_msg:
            return None

        author: Dict[str, Any] = raw_msg.get("author") or {}
        role: str = author.get("role") or "system"
        actor = _ROLE_MAP.get(role, "system")

        content = self._extract_content(raw_msg.get("content") or {})
        if not content:
            return None

        create_time: float = raw_msg.get("create_time") or 0.0
        timestamp = _ts_to_dt(create_time)

        msg_metadata: Dict[str, Any] = {}
        raw_meta: Dict[str, Any] = raw_msg.get("metadata") or {}
        if raw_meta.get("model_slug"):
            msg_metadata["model_slug"] = raw_meta["model_slug"]
        if raw_meta.get("is_visually_hidden_from_conversation"):
            msg_metadata["hidden"] = True

        return ParsedMessage(
            external_id=raw_msg.get("id") or "",
            actor=actor,
            content=content,
            timestamp=timestamp,
            metadata=msg_metadata,
        )

    @staticmethod
    def _extract_content(content_dict: Dict[str, Any]) -> str:
        """Extract plain text from a ChatGPT content object.

        Handles the following content_type values:
        - "text": joins the parts array as a single string.
        - "multimodal_text": joins text parts, skips image/binary parts.
        - others (tether_quote, code, etc.): returns empty string in v1.

        Args:
            content_dict: The 'content' sub-dict of a message node.

        Returns:
            Plain-text string, or empty string if not extractable.
        """
        content_type: str = content_dict.get("content_type") or ""
        parts: Any = content_dict.get("parts") or []

        if content_type == "text":
            return _join_parts(parts)

        if content_type == "multimodal_text":
            text_parts = [
                p for p in parts
                if isinstance(p, str)
            ]
            return _join_parts(text_parts)

        # Unsupported types (tether_browsing_display, code, etc.) — skip
        return ""

    @staticmethod
    def _compute_hash(
        external_id: str, messages: List[ParsedMessage]
    ) -> str:
        """Compute a SHA-256 hash for deduplication.

        The hash is derived from the conversation's external_id and the
        concatenated (actor + content) of every message. This means the
        same conversation imported twice will produce the same hash and
        be deduplicated by the pipeline.

        Args:
            external_id: The provider-assigned conversation ID.
            messages: Ordered list of parsed messages.

        Returns:
            Hex-encoded SHA-256 digest (64 characters).
        """
        h = hashlib.sha256()
        h.update(b"chatgpt\x00")
        h.update(external_id.encode("utf-8"))
        h.update(b"\x00")
        for msg in messages:
            h.update(msg.actor.encode("utf-8"))
            h.update(b"\x1f")
            h.update(msg.content.encode("utf-8"))
            h.update(b"\x1e")
        return h.hexdigest()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _ts_to_dt(ts: float) -> datetime:
    """Convert a Unix timestamp float to a UTC-aware datetime.

    Args:
        ts: Unix timestamp (seconds since epoch). Zero produces the epoch.

    Returns:
        timezone-aware datetime in UTC.
    """
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return datetime.fromtimestamp(0, tz=timezone.utc)


def _join_parts(parts: Any) -> str:
    """Join a list of string parts into a single trimmed string.

    Non-string elements are silently skipped (e.g. image dicts).

    Args:
        parts: A list that may contain strings and other objects.

    Returns:
        Concatenated string with leading/trailing whitespace stripped.
    """
    if not isinstance(parts, list):
        return ""
    return "".join(p for p in parts if isinstance(p, str)).strip()
