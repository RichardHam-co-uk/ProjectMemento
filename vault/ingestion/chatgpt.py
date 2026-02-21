"""
ChatGPT export adapter for the LLM Memory Vault.

Parses the JSON export format produced by ChatGPT's "Export data" feature.
The export is a JSON array of conversation objects, each containing a
tree-structured "mapping" of messages linked by parent/children references.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vault.ingestion.base import (
    ParsedConversation,
    ParsedMessage,
    deduplicate_messages,
    generate_conversation_hash,
    normalize_timestamp,
)

_MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
_VALID_ROLES = {"user", "assistant", "system"}


class ChatGPTAdapter:
    """Adapter for importing ChatGPT conversation exports.

    Supports the JSON array format produced by ChatGPT's data export
    feature, where each conversation contains a tree-structured "mapping"
    of message nodes linked by parent/children IDs.
    """

    @property
    def provider_name(self) -> str:
        """Return the provider identifier.

        Returns:
            The string "chatgpt".
        """
        return "chatgpt"

    def validate_format(self, file_path: Path) -> bool:
        """Check whether the file looks like a ChatGPT export.

        A valid file is JSON, its top-level value is a list, and every
        element is an object with a "mapping" key.

        Args:
            file_path: Path to the file to validate.

        Returns:
            True if the file is a valid ChatGPT export, False otherwise.
        """
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return False

        if not isinstance(data, list):
            return False

        if len(data) == 0:
            return True  # Empty export is technically valid

        return all(isinstance(item, dict) and "mapping" in item for item in data)

    def parse(self, file_path: Path) -> list[ParsedConversation]:
        """Parse a ChatGPT export file into ParsedConversation objects.

        Args:
            file_path: Path to the ChatGPT JSON export file.

        Returns:
            List of ParsedConversation objects, one per conversation in
            the export. Conversations with no valid messages are included
            with an empty messages list.

        Raises:
            ValueError: If the file is larger than 100 MB, is not valid
                JSON, or does not match the expected format.
            OSError: If the file cannot be read.
        """
        if file_path.stat().st_size > _MAX_FILE_SIZE:
            raise ValueError(
                f"Export file is too large (> 100 MB): {file_path}"
            )

        try:
            raw_text = file_path.read_text(encoding="utf-8")
            data = json.loads(raw_text)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid JSON in export file: {e}") from e

        if not isinstance(data, list):
            raise ValueError(
                "Expected ChatGPT export to be a JSON array at the top level."
            )

        conversations: list[ParsedConversation] = []
        for conv_obj in data:
            parsed = self._parse_conversation(conv_obj)
            if parsed is not None:
                conversations.append(parsed)

        return conversations

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_conversation(
        self, conv_obj: dict[str, Any]
    ) -> ParsedConversation | None:
        """Parse a single conversation object from the export.

        Args:
            conv_obj: Raw conversation dictionary from the JSON export.

        Returns:
            A ParsedConversation, or None if the object is structurally
            invalid.
        """
        if not isinstance(conv_obj, dict):
            return None

        mapping: dict[str, Any] = conv_obj.get("mapping", {}) or {}
        if not isinstance(mapping, dict):
            mapping = {}

        title: str = conv_obj.get("title") or "Untitled"
        external_id: str | None = conv_obj.get("conversation_id") or None
        created_at = normalize_timestamp(conv_obj.get("create_time"))
        updated_at = normalize_timestamp(conv_obj.get("update_time"))

        messages = self._flatten_mapping(mapping)
        messages = deduplicate_messages(messages)

        metadata: dict[str, Any] = {}
        if "id" in conv_obj:
            metadata["id"] = conv_obj["id"]

        return ParsedConversation(
            title=title,
            source=self.provider_name,
            external_id=external_id,
            created_at=created_at,
            updated_at=updated_at,
            messages=messages,
            metadata=metadata,
        )

    def _flatten_mapping(
        self, mapping: dict[str, Any]
    ) -> list[ParsedMessage]:
        """Flatten the tree-structured mapping into a chronological list.

        ChatGPT exports use a linked-list / tree structure where each node
        references its parent and children. This method performs a
        depth-first traversal from the root node(s) to produce a linear,
        chronological sequence of messages.

        Nodes are skipped if:
        - The "message" field is null/None (deleted messages, root nodes)
        - The author role is not "user", "assistant", or "system"
        - The content cannot be extracted as non-empty text

        Args:
            mapping: The raw mapping dictionary from the conversation object.

        Returns:
            Ordered list of ParsedMessage objects.
        """
        if not mapping:
            return []

        # Find root nodes (nodes with no parent or whose parent is not in mapping)
        root_ids = [
            node_id
            for node_id, node in mapping.items()
            if not node.get("parent") or node["parent"] not in mapping
        ]

        messages: list[ParsedMessage] = []

        def walk(node_id: str) -> None:
            node = mapping.get(node_id)
            if node is None:
                return

            msg_data = node.get("message")
            if msg_data is not None:
                parsed = self._parse_message_node(msg_data)
                if parsed is not None:
                    messages.append(parsed)

            for child_id in (node.get("children") or []):
                walk(child_id)

        for root_id in root_ids:
            walk(root_id)

        # Sort by timestamp for a deterministic chronological order
        messages.sort(key=lambda m: m.timestamp)
        return messages

    def _parse_message_node(
        self, msg_data: dict[str, Any]
    ) -> ParsedMessage | None:
        """Parse a single message node dict into a ParsedMessage.

        Args:
            msg_data: The "message" sub-dict from a mapping node.

        Returns:
            A ParsedMessage, or None if the message should be skipped.
        """
        if not isinstance(msg_data, dict):
            return None

        # Extract role / actor
        author = msg_data.get("author") or {}
        role = author.get("role", "") if isinstance(author, dict) else ""
        if role not in _VALID_ROLES:
            return None

        # Extract content text
        content = self._extract_content(msg_data.get("content") or {})
        if not content:
            return None

        msg_id: str = msg_data.get("id") or ""
        timestamp = normalize_timestamp(msg_data.get("create_time"))

        # Collect metadata
        raw_meta = msg_data.get("metadata") or {}
        metadata: dict[str, Any] = {}
        if isinstance(raw_meta, dict):
            if "model_slug" in raw_meta:
                metadata["model_slug"] = raw_meta["model_slug"]
            if "timestamp_" in raw_meta:
                metadata["timestamp_type"] = raw_meta["timestamp_"]

        return ParsedMessage(
            id=msg_id,
            actor=role,
            content=content,
            timestamp=timestamp,
            metadata=metadata,
        )

    @staticmethod
    def _extract_content(content_obj: dict[str, Any] | Any) -> str:
        """Extract plain text from a ChatGPT content object.

        ChatGPT content objects have a "content_type" and a "parts" list.
        Each part may be a string or a complex object (e.g., code interpreter
        output). This method joins all string parts into a single string.

        Args:
            content_obj: The "content" field from a message node.

        Returns:
            Extracted text, or empty string if nothing usable is found.
        """
        if not isinstance(content_obj, dict):
            return ""

        parts = content_obj.get("parts") or []
        if not isinstance(parts, list):
            return ""

        text_parts: list[str] = []
        for part in parts:
            if isinstance(part, str) and part.strip():
                text_parts.append(part.strip())
            elif isinstance(part, dict):
                # Handle code interpreter outputs or other structured parts
                # Try common text fields
                for key in ("text", "content", "value"):
                    if key in part and isinstance(part[key], str) and part[key].strip():
                        text_parts.append(part[key].strip())
                        break

        return "\n".join(text_parts)
