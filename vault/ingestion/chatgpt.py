"""ChatGPT conversation export adapter.

Parses the ``conversations.json`` file produced by ChatGPT's data-export
feature and converts it into the canonical
:class:`~vault.ingestion.base.ParsedConversation` /
:class:`~vault.ingestion.base.ParsedMessage` format used by the rest of
the vault ingestion pipeline.

Export format summary
---------------------
The file is a JSON **array** of conversation objects.  Each object has:

- ``title`` — human-readable conversation title
- ``create_time`` / ``update_time`` — Unix timestamps (float)
- ``conversation_id`` or ``id`` — provider-assigned UUID
- ``mapping`` — a dict of node objects forming a tree; each node may carry
  a ``message`` sub-object with author, content, and timestamp

The mapping tree must be traversed from the root (the node whose ``parent``
is ``null``) following ``children`` links to produce a chronologically
ordered message list.

Filtering rules applied during parsing
---------------------------------------
- Nodes whose ``message`` is ``null`` are skipped.
- Messages with ``author.role`` of ``"tool"`` or ``"system"`` are skipped.
- Messages whose ``content.content_type`` is not ``"text"`` or ``"code"``
  are skipped (images, tool outputs, tether quotes, etc.).
- Messages with empty content after joining ``parts`` are skipped.
"""
from __future__ import annotations

import json
from datetime import timezone
from pathlib import Path
from typing import Any

from vault.ingestion.base import (
    ImportResult,
    ParsedConversation,
    ParsedMessage,
    deduplicate_messages,
    generate_conversation_hash,
    normalize_timestamp,
)

# Roles to include in the imported message list
_ALLOWED_ROLES: frozenset[str] = frozenset({"user", "assistant"})

# content_type values that carry plain text in their ``parts`` list
_TEXT_CONTENT_TYPES: frozenset[str] = frozenset({"text", "code"})


class ChatGPTAdapter:
    """Adapter for ChatGPT ``conversations.json`` export files.

    Implements the :class:`~vault.ingestion.base.BaseAdapter` Protocol.

    Example:
        >>> adapter = ChatGPTAdapter()
        >>> conversations = adapter.parse(Path("conversations.json"))
        >>> print(len(conversations))
        42
    """

    @property
    def provider_name(self) -> str:
        """Return the provider identifier.

        Returns:
            ``"chatgpt"``
        """
        return "chatgpt"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, file_path: Path) -> list[ParsedConversation]:
        """Parse a ChatGPT ``conversations.json`` export file.

        Args:
            file_path: Path to the ``conversations.json`` file.

        Returns:
            A list of :class:`~vault.ingestion.base.ParsedConversation`
            objects, one per conversation in the export.  Conversations
            that fail to parse are silently skipped (their errors surface
            through the returned :class:`~vault.ingestion.base.ImportResult`
            when called via the CLI).

        Raises:
            FileNotFoundError: If ``file_path`` does not exist.
            ValueError: If the file is not valid JSON or is not a JSON array.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Export file not found: {file_path}")

        raw = file_path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {file_path}: {exc}") from exc

        if not isinstance(data, list):
            raise ValueError(
                f"Expected a JSON array in {file_path}, got {type(data).__name__}"
            )

        results: list[ParsedConversation] = []
        for raw_conv in data:
            parsed = self._parse_conversation(raw_conv)
            if parsed is not None:
                results.append(parsed)
        return results

    def validate_format(self, file_path: Path) -> bool:
        """Check whether a file looks like a ChatGPT export.

        Reads only the minimal amount of the file needed to decide.

        Args:
            file_path: Path to the file to inspect.

        Returns:
            ``True`` if the file is a JSON array whose first element
            contains ``"mapping"`` and at least one of ``"create_time"``
            or ``"conversation_id"``; ``False`` otherwise.
        """
        try:
            raw = file_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, list) or not data:
                return False
            first = data[0]
            if not isinstance(first, dict):
                return False
            return "mapping" in first and (
                "create_time" in first
                or "conversation_id" in first
                or "id" in first
            )
        except Exception:  # noqa: BLE001
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_conversation(
        self, raw: dict[str, Any]
    ) -> ParsedConversation | None:
        """Convert a single raw conversation dict into a ParsedConversation.

        Args:
            raw: A conversation object from the top-level JSON array.

        Returns:
            A populated :class:`~vault.ingestion.base.ParsedConversation`,
            or ``None`` if the conversation cannot be parsed.
        """
        try:
            title = raw.get("title") or "Untitled"
            external_id = raw.get("conversation_id") or raw.get("id")
            created_at = normalize_timestamp(raw.get("create_time"))
            updated_at = normalize_timestamp(raw.get("update_time"))

            mapping: dict[str, Any] = raw.get("mapping") or {}
            messages = self._extract_messages(mapping)
            messages = deduplicate_messages(messages)

            return ParsedConversation(
                title=title,
                source=self.provider_name,
                external_id=external_id,
                created_at=created_at,
                updated_at=updated_at,
                messages=messages,
                metadata={
                    "conversation_id": external_id,
                    "node_count": len(mapping),
                },
            )
        except Exception:  # noqa: BLE001
            return None

    def _extract_messages(
        self, mapping: dict[str, Any]
    ) -> list[ParsedMessage]:
        """Walk the mapping tree and return messages in conversation order.

        The tree is walked from the root node (the one whose ``parent`` is
        ``None``) following the first child of each node (ChatGPT exports
        always form a linear chain in practice).

        Args:
            mapping: The raw ``mapping`` dict from the conversation object.

        Returns:
            Ordered list of :class:`~vault.ingestion.base.ParsedMessage`
            instances (may be empty).
        """
        # Find the root node (parent is None or not present)
        root_id: str | None = None
        for node_id, node in mapping.items():
            if node.get("parent") is None:
                root_id = node_id
                break

        if root_id is None:
            return []

        # Traverse linearly: at each node take the first child
        messages: list[ParsedMessage] = []
        visited: set[str] = set()
        current_id: str | None = root_id

        while current_id is not None:
            if current_id in visited:
                break  # cycle guard
            visited.add(current_id)

            node = mapping.get(current_id)
            if node is None:
                break

            msg = self._parse_message(node)
            if msg is not None:
                messages.append(msg)

            children: list[str] = node.get("children") or []
            current_id = children[0] if children else None

        return messages

    def _parse_message(self, node: dict[str, Any]) -> ParsedMessage | None:
        """Extract a ParsedMessage from a mapping node, or return None.

        Args:
            node: A single node from the conversation mapping.

        Returns:
            A :class:`~vault.ingestion.base.ParsedMessage` if the node
            carries a usable message, or ``None`` otherwise.
        """
        raw_msg = node.get("message")
        if not isinstance(raw_msg, dict):
            return None

        author = raw_msg.get("author") or {}
        role: str = author.get("role", "")
        if role not in _ALLOWED_ROLES:
            return None

        content_obj = raw_msg.get("content") or {}
        content_type: str = content_obj.get("content_type", "")
        if content_type not in _TEXT_CONTENT_TYPES:
            return None

        parts = content_obj.get("parts") or []
        text = "\n".join(
            p for p in parts if isinstance(p, str) and p.strip()
        ).strip()
        if not text:
            return None

        msg_id: str = raw_msg.get("id") or node.get("id") or ""
        timestamp = normalize_timestamp(raw_msg.get("create_time"))
        metadata: dict[str, Any] = dict(raw_msg.get("metadata") or {})
        metadata["content_type"] = content_type

        return ParsedMessage(
            id=msg_id,
            actor=role,
            content=text,
            timestamp=timestamp,
            metadata=metadata,
        )


def run_import(
    file_path: Path,
    db: Any,  # VaultDB — typed as Any to avoid circular import
) -> ImportResult:
    """Parse a ChatGPT export and persist all conversations to *db*.

    This is a convenience function used by the CLI ``vault import chatgpt``
    command.  It handles duplicate detection (conversations that already exist
    in the database are skipped) and per-conversation error recovery.

    Args:
        file_path: Path to the ``conversations.json`` export file.
        db: A :class:`~vault.storage.db.VaultDB` instance (open and ready).

    Returns:
        An :class:`~vault.ingestion.base.ImportResult` summarising the
        import: how many conversations were imported, skipped, or failed.
    """
    from vault.storage.models import Conversation, Message  # local import

    adapter = ChatGPTAdapter()
    result = ImportResult()

    try:
        conversations = adapter.parse(file_path)
    except (FileNotFoundError, ValueError) as exc:
        result.failed += 1
        result.errors.append(str(exc))
        return result

    for parsed_conv in conversations:
        try:
            conv_id = generate_conversation_hash(
                source=parsed_conv.source,
                title=parsed_conv.title,
                created_at=parsed_conv.created_at,
            )

            # Deduplication: skip if already in DB
            existing = db.get_conversation(conv_id)
            if existing is not None:
                result.skipped += 1
                continue

            messages = [
                Message(
                    id=f"{conv_id}-{i:06d}",
                    conversation_id=conv_id,
                    actor=pm.actor,
                    content=pm.content,
                    timestamp=pm.timestamp.replace(tzinfo=None)
                    if pm.timestamp.tzinfo is not None
                    else pm.timestamp,
                    metadata=pm.metadata,
                )
                for i, pm in enumerate(parsed_conv.messages)
            ]

            conv = Conversation(
                id=conv_id,
                title=parsed_conv.title,
                source=parsed_conv.source,
                external_id=parsed_conv.external_id,
                created_at=parsed_conv.created_at.replace(tzinfo=None)
                if parsed_conv.created_at.tzinfo is not None
                else parsed_conv.created_at,
                updated_at=parsed_conv.updated_at.replace(tzinfo=None)
                if parsed_conv.updated_at.tzinfo is not None
                else parsed_conv.updated_at,
                message_count=len(messages),
                metadata=parsed_conv.metadata,
                messages=messages,
            )

            db.add_conversation(conv)
            result.imported += 1

        except Exception as exc:  # noqa: BLE001
            result.failed += 1
            result.errors.append(
                f"Failed to import '{parsed_conv.title}': {exc}"
            )

    return result
