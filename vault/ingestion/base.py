"""Base adapter interface and shared data types for provider ingestion.

Defines the :class:`BaseAdapter` Protocol and the data classes
(:class:`ParsedMessage`, :class:`ParsedConversation`, :class:`ImportResult`)
that all provider-specific adapters must produce and consume.

Also provides utility functions for timestamp normalisation, conversation
hashing, and message deduplication.

This module is intentionally standalone — it has no imports from other
``vault`` sub-packages so that it can be imported without side effects.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ParsedMessage:
    """A single message extracted from a provider export.

    Args:
        id: Provider-assigned message identifier (opaque string or UUID).
        actor: Role of the message author.  One of ``"user"``,
            ``"assistant"``, or ``"system"``.
        content: Plaintext content of the message.
        timestamp: UTC datetime when the message was created.
        metadata: Arbitrary provider-specific key/value data attached to
            the message (e.g. model slug, finish reason).
    """

    id: str
    actor: str
    content: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedConversation:
    """A full conversation thread parsed from a provider export.

    Args:
        title: Human-readable conversation title.
        source: Provider identifier, e.g. ``"chatgpt"`` or ``"claude"``.
        external_id: Provider-assigned conversation ID, or ``None`` if not
            available.
        created_at: UTC datetime when the conversation was first created.
        updated_at: UTC datetime when the conversation was last updated.
        messages: Ordered list of parsed messages (oldest first).
        metadata: Arbitrary provider-specific key/value data attached to
            the conversation.
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
    """Summary statistics from a completed import operation.

    Args:
        imported: Number of conversations successfully imported.
        skipped: Number of conversations skipped (e.g. already present).
        failed: Number of conversations that could not be imported due to
            errors.
        errors: Human-readable error messages, one per failure.
    """

    imported: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class BaseAdapter(Protocol):
    """Structural interface for LLM provider conversation importers.

    All concrete adapters (e.g. ``ChatGPTAdapter``) must satisfy this
    Protocol.  Duck-typing is used — explicit inheritance is not required.
    """

    @property
    def provider_name(self) -> str:
        """Unique, lowercase provider identifier.

        Returns:
            A short string such as ``"chatgpt"`` or ``"claude"`` that is
            stored as the ``source`` field on every imported conversation.
        """
        ...

    def parse(self, file_path: Path) -> list[ParsedConversation]:
        """Parse a provider export file into a list of conversations.

        Args:
            file_path: Path to the provider-specific export file (e.g. a
                ``conversations.json`` from a ChatGPT data export).

        Returns:
            A list of :class:`ParsedConversation` objects ready for storage.

        Raises:
            FileNotFoundError: If ``file_path`` does not exist.
            ValueError: If the file content cannot be parsed as a valid
                export for this provider.
        """
        ...

    def validate_format(self, file_path: Path) -> bool:
        """Check whether a file matches the expected format for this provider.

        Args:
            file_path: Path to the file to inspect.

        Returns:
            ``True`` if the file appears to be a valid export for this
            provider, ``False`` otherwise.  Should not raise on malformed
            input — return ``False`` instead.
        """
        ...


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def normalize_timestamp(raw: float | str | int | None) -> datetime:
    """Convert various timestamp formats to a timezone-aware UTC datetime.

    Handles the following input types:

    - **float / int** — interpreted as a Unix epoch timestamp
      (seconds since 1970-01-01T00:00:00Z).
    - **str** — parsed with :func:`datetime.fromisoformat`.  If the string
      carries no timezone information, UTC is assumed.
    - **None** — returns the current UTC time.

    Args:
        raw: The timestamp value to convert.

    Returns:
        A :class:`~datetime.datetime` instance with
        ``tzinfo=timezone.utc``.

    Raises:
        ValueError: If a string value cannot be parsed as an ISO 8601
            datetime.
    """
    if raw is None:
        return datetime.now(timezone.utc)

    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw), tz=timezone.utc)

    # str branch
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def generate_conversation_hash(
    source: str, title: str, created_at: datetime
) -> str:
    """Generate a stable SHA-256 fingerprint for conversation deduplication.

    The hash is computed over the concatenation
    ``"<source>:<title>:<created_at.isoformat()>"`` so that the same
    conversation imported twice produces the same hash regardless of when
    the import is performed.

    Args:
        source: Provider name, e.g. ``"chatgpt"``.
        title: Conversation title as reported by the provider.
        created_at: UTC creation timestamp of the conversation.

    Returns:
        A 64-character lowercase hexadecimal string (SHA-256 digest).
    """
    payload = f"{source}:{title}:{created_at.isoformat()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def deduplicate_messages(messages: list[ParsedMessage]) -> list[ParsedMessage]:
    """Remove duplicate messages while preserving the original order.

    Two messages are considered duplicates if they share the same
    ``(actor, timestamp, content[:100])`` tuple.  Only the first occurrence
    of each unique tuple is kept.

    Args:
        messages: Ordered list of parsed messages (may contain duplicates).

    Returns:
        A new list with duplicate messages removed, preserving the order of
        first occurrence.
    """
    seen: set[tuple[str, datetime, str]] = set()
    result: list[ParsedMessage] = []
    for msg in messages:
        key = (msg.actor, msg.timestamp, msg.content[:100])
        if key not in seen:
            seen.add(key)
            result.append(msg)
    return result
