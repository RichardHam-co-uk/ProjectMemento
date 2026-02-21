"""Base adapter interface and shared data types for LLM provider conversation importers.

Defines the common protocol that all provider adapters (ChatGPT, Claude, etc.)
must implement, along with shared dataclasses for parsed conversations and
utility functions for timestamp normalization and deduplication.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


@dataclass
class ParsedMessage:
    """A single message extracted from a provider export.

    Attributes:
        id: Unique message identifier.
        actor: Who sent the message — "user", "assistant", or "system".
        content: The text content of the message.
        timestamp: UTC timestamp of the message.
        metadata: Optional provider-specific metadata.
    """

    id: str
    actor: str  # "user", "assistant", or "system"
    content: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedConversation:
    """A conversation thread extracted from a provider export.

    Attributes:
        title: Conversation title or subject.
        source: Provider identifier (e.g., "chatgpt", "claude").
        external_id: Provider's own conversation ID, if available.
        created_at: UTC timestamp when the conversation was created.
        updated_at: UTC timestamp of the last update.
        messages: Ordered list of messages in the conversation.
        metadata: Optional provider-specific metadata.
    """

    title: str
    source: str  # e.g. "chatgpt", "claude"
    external_id: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[ParsedMessage]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportResult:
    """Summary of an import operation.

    Attributes:
        imported: Number of conversations successfully imported.
        skipped: Number of conversations skipped (e.g., duplicates).
        failed: Number of conversations that failed to import.
        errors: List of error messages for failed imports.
    """

    imported: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class BaseAdapter(Protocol):
    """Interface for LLM provider conversation importers.

    All provider adapters must implement this protocol to be usable
    with the import pipeline.
    """

    @property
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'chatgpt')."""
        ...

    def parse(self, file_path: Path) -> list[ParsedConversation]:
        """Parse a provider export file into conversations.

        Args:
            file_path: Path to the provider's export file.

        Returns:
            List of parsed conversations extracted from the file.
        """
        ...

    def validate_format(self, file_path: Path) -> bool:
        """Check if a file is a valid format for this provider.

        Args:
            file_path: Path to the file to validate.

        Returns:
            True if the file is a valid export for this provider.
        """
        ...


def normalize_timestamp(raw: float | str | int | None) -> datetime:
    """Convert various timestamp formats to a UTC datetime.

    Handles:
        - Unix epoch floats (e.g., 1234567890.123)
        - ISO format strings (e.g., "2024-01-15T12:00:00+00:00")
        - Integer timestamps (e.g., 1234567890)
        - None (returns datetime.now(UTC))

    Args:
        raw: A timestamp in one of the supported formats, or None.

    Returns:
        A timezone-aware UTC datetime.
    """
    if raw is None:
        return datetime.now(timezone.utc)

    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw), tz=timezone.utc)

    if isinstance(raw, str):
        return datetime.fromisoformat(raw)

    return datetime.now(timezone.utc)


def generate_conversation_hash(source: str, title: str, created_at: datetime) -> str:
    """Generate a SHA-256 hash for conversation deduplication.

    Creates a deterministic hash from the conversation's identifying
    attributes. Two conversations with the same source, title, and
    creation time will produce the same hash.

    Args:
        source: Provider name (e.g., "chatgpt").
        title: Conversation title.
        created_at: Conversation creation timestamp.

    Returns:
        64-character hex digest string.
    """
    payload = f"{source}:{title}:{created_at.isoformat()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def deduplicate_messages(messages: list[ParsedMessage]) -> list[ParsedMessage]:
    """Remove duplicate messages based on (actor, timestamp, content[:100]).

    Uses a composite key of the actor, timestamp, and first 100 characters
    of content to identify duplicates. Preserves the order of first
    occurrences.

    Args:
        messages: List of parsed messages, potentially containing duplicates.

    Returns:
        Deduplicated list preserving original order.
    """
    seen: set[tuple[str, str, str]] = set()
    result: list[ParsedMessage] = []

    for msg in messages:
        key = (msg.actor, msg.timestamp.isoformat(), msg.content[:100])
        if key not in seen:
            seen.add(key)
            result.append(msg)

    return result
