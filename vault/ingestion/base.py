"""
Base adapter interface and shared data types for the LLM Memory Vault ingestion system.

Defines the common Protocol that all provider adapters must implement,
along with shared dataclasses and utility functions for timestamp
normalization, conversation hashing, and deduplication.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class ParsedMessage:
    """A single message extracted from a provider export.

    Attributes:
        id: Provider-assigned message identifier.
        actor: Who generated the message — "user", "assistant", or "system".
        content: Plain-text content of the message.
        timestamp: Message creation time in UTC.
        metadata: Additional provider-specific key/value pairs.
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
        title: Human-readable conversation title.
        source: Provider identifier (e.g., "chatgpt", "claude").
        external_id: Provider-assigned conversation ID, or None.
        created_at: Conversation creation time in UTC.
        updated_at: Last update time in UTC.
        messages: Ordered list of messages in the conversation.
        metadata: Additional provider-specific key/value pairs.
    """

    title: str
    source: str
    external_id: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[ParsedMessage]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportResult:
    """Result summary from an import operation.

    Attributes:
        imported: Number of conversations successfully imported.
        skipped: Number of conversations skipped (e.g., duplicates).
        failed: Number of conversations that failed to import.
        errors: List of human-readable error messages for failures.
    """

    imported: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class BaseAdapter(Protocol):
    """Interface for LLM provider conversation importers.

    All provider adapters must implement this protocol to be usable by
    the ImportPipeline.
    """

    @property
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'chatgpt', 'claude').

        Returns:
            Lowercase string identifying the provider.
        """
        ...

    def parse(self, file_path: Path) -> list[ParsedConversation]:
        """Parse a provider export file into a list of conversations.

        Args:
            file_path: Path to the provider export file.

        Returns:
            List of ParsedConversation objects ready for import.

        Raises:
            ValueError: If the file format is invalid or unreadable.
        """
        ...

    def validate_format(self, file_path: Path) -> bool:
        """Check whether the file is a valid export for this provider.

        Args:
            file_path: Path to the file to validate.

        Returns:
            True if the file appears to be a valid export, False otherwise.
        """
        ...


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------


def normalize_timestamp(raw: float | str | int | None) -> datetime:
    """Convert various timestamp formats to a timezone-aware UTC datetime.

    Handles:
        - Unix epoch floats (e.g., 1234567890.123)
        - Unix epoch integers (e.g., 1234567890)
        - ISO 8601 strings (e.g., "2024-01-15T10:30:00+00:00")
        - None (returns datetime.now(UTC))

    Args:
        raw: Timestamp in one of the supported formats, or None.

    Returns:
        UTC-aware datetime object.
    """
    if raw is None:
        return datetime.now(timezone.utc)

    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw), tz=timezone.utc)

    if isinstance(raw, str):
        try:
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            # Fall back to treating as a numeric string
            try:
                return datetime.fromtimestamp(float(raw), tz=timezone.utc)
            except ValueError:
                return datetime.now(timezone.utc)

    return datetime.now(timezone.utc)


def generate_conversation_hash(
    source: str, title: str, created_at: datetime
) -> str:
    """Generate a SHA-256 content hash for conversation deduplication.

    The hash is computed over the canonical string
    ``"<source>:<title>:<created_at.isoformat()>"``.

    Args:
        source: Provider name (e.g., "chatgpt").
        title: Conversation title.
        created_at: Conversation creation timestamp.

    Returns:
        64-character hex digest string.
    """
    canonical = f"{source}:{title}:{created_at.isoformat()}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def deduplicate_messages(messages: list[ParsedMessage]) -> list[ParsedMessage]:
    """Remove duplicate messages based on (actor, timestamp, content[:100]).

    Preserves the first occurrence of each unique message and maintains the
    original ordering.

    Args:
        messages: List of ParsedMessage objects, potentially containing
            duplicates.

    Returns:
        Deduplicated list preserving original insertion order.
    """
    seen: set[tuple[str, str, str]] = set()
    result: list[ParsedMessage] = []
    for msg in messages:
        key = (msg.actor, msg.timestamp.isoformat(), msg.content[:100])
        if key not in seen:
            seen.add(key)
            result.append(msg)
    return result
