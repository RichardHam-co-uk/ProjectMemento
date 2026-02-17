"""
Base adapter interface for LLM provider ingestion.

Defines the protocol (abstract base class) that all provider-specific
adapters must implement, plus the shared dataclasses used to exchange
parsed conversation data between adapters and the import pipeline.

Note: Task 1.6.1 (Tier 2) owns this file. This implementation is the
minimal functional version needed by the ChatGPT adapter and import
pipeline; the Tier 2 task may extend it with additional utility helpers.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class ParsedMessage:
    """A single message extracted from a provider export.

    Attributes:
        external_id: Provider-assigned message ID (e.g. UUID from ChatGPT).
        actor: Who produced this message — 'user', 'assistant', or 'system'.
        content: Plain-text content of the message.
        timestamp: UTC datetime when the message was created.
        metadata: Provider-specific extras (model slug, plugin info, etc.).
    """

    external_id: str
    actor: str
    content: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)


@dataclass
class ParsedConversation:
    """A conversation extracted from a provider export.

    Attributes:
        external_id: Provider-assigned conversation ID.
        title: Human-readable conversation title.
        created_at: UTC datetime of first message.
        updated_at: UTC datetime of last update.
        messages: Ordered list of messages (chronological).
        metadata: Provider-specific extras (model used, plugin list, etc.).
        content_hash: SHA-256 hex digest of the canonical content;
            set by the adapter after all messages are collected.
    """

    external_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ParsedMessage] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    content_hash: str = ""


class BaseAdapter(ABC):
    """Abstract base class for LLM provider ingestion adapters.

    Subclasses must implement provider_name, validate_format, and parse.
    The import pipeline calls validate_format first, then parse.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider (e.g. 'chatgpt', 'claude')."""
        ...

    @abstractmethod
    def validate_format(self, file_path: Path) -> bool:
        """Return True if file_path looks like a valid export for this provider.

        Should perform lightweight checks (file extension, top-level JSON
        structure) without loading the entire file into memory.

        Args:
            file_path: Path to the export file.

        Returns:
            True if the file appears valid; False otherwise.
        """
        ...

    @abstractmethod
    def parse(self, file_path: Path) -> List[ParsedConversation]:
        """Parse the export file and return a list of ParsedConversation objects.

        Args:
            file_path: Path to the validated export file.

        Returns:
            List of ParsedConversation objects in the order they appear
            in the export (not necessarily chronological across conversations).

        Raises:
            ValueError: If the file cannot be parsed or is malformed.
            OSError: If the file cannot be read.
        """
        ...
