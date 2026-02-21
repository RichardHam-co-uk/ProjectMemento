"""
Import pipeline for the LLM Memory Vault.

Orchestrates parsing, deduplication, encryption, and database persistence
of conversations from any registered adapter. Supports a progress callback
for CLI progress bars.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from pathlib import Path
from typing import Callable

from vault.ingestion.base import BaseAdapter, ImportResult, ParsedConversation
from vault.storage.blobs import BlobStore
from vault.storage.db import VaultDB
from vault.storage.models import (
    ActorType,
    Conversation,
    Message,
    SensitivityLevel,
)

logger = logging.getLogger(__name__)

# Map base.py actor strings to the ActorType ORM enum
_ACTOR_MAP: dict[str, ActorType] = {
    "user": ActorType.USER,
    "assistant": ActorType.ASSISTANT,
    "system": ActorType.SYSTEM,
}


class ImportPipeline:
    """Orchestrates importing conversations from an adapter into the vault.

    Handles:
    - Calling the adapter to parse provider export files
    - Deduplication via content hashes stored in the database
    - Encrypting message content via BlobStore
    - Persisting Conversation and Message ORM objects atomically

    Attributes:
        db: VaultDB instance for database operations.
        blob_store: BlobStore instance for encrypted blob storage.
        master_key: 32-byte master key for content encryption.
    """

    def __init__(
        self, db: VaultDB, blob_store: BlobStore, master_key: bytes
    ) -> None:
        """Initialize the import pipeline.

        Args:
            db: Initialized VaultDB instance.
            blob_store: Initialized BlobStore instance.
            master_key: 32-byte master key for encrypting message content.
        """
        self.db = db
        self.blob_store = blob_store
        self.master_key = master_key

    def import_conversations(
        self,
        adapter: BaseAdapter,
        file_path: Path,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> ImportResult:
        """Parse and import conversations from an adapter export file.

        For each parsed conversation:
        1. Computes a content hash and checks for duplicates.
        2. Skips duplicates (increments skipped counter).
        3. Encrypts each message's content into the BlobStore.
        4. Persists the Conversation and Message ORM objects atomically.
        5. Calls on_progress(current_index, total) after each conversation.

        If a single conversation fails, the error is logged and the failure
        counter is incremented, but processing continues for the remaining
        conversations.

        Args:
            adapter: The adapter to use for parsing the file.
            file_path: Path to the provider export file.
            on_progress: Optional callback invoked after each conversation
                is processed. Receives (current_index, total).

        Returns:
            ImportResult summarising imported, skipped, and failed counts
            and any error messages.
        """
        result = ImportResult()

        try:
            conversations = adapter.parse(file_path)
        except Exception as exc:
            error_msg = f"Failed to parse export file: {exc}"
            logger.error(error_msg)
            result.failed += 1
            result.errors.append(error_msg)
            return result

        total = len(conversations)

        for index, parsed_conv in enumerate(conversations):
            try:
                self._import_single_conversation(parsed_conv, result)
            except Exception as exc:
                error_msg = (
                    f"Failed to import conversation '{parsed_conv.title}': {exc}"
                )
                logger.error(error_msg, exc_info=True)
                result.failed += 1
                result.errors.append(error_msg)

            if on_progress is not None:
                try:
                    on_progress(index + 1, total)
                except Exception:
                    pass  # Progress callback errors must not abort the import

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _import_single_conversation(
        self, parsed: ParsedConversation, result: ImportResult
    ) -> None:
        """Import a single ParsedConversation into the vault.

        Args:
            parsed: The ParsedConversation to import.
            result: The ImportResult accumulator to update in place.
        """
        # Generate content hash for deduplication
        content_hash = _compute_conversation_hash(parsed)

        # Check for existing duplicate
        if self.db.conversation_hash_exists(content_hash):
            result.skipped += 1
            return

        # Build a stable conversation ID from the hash
        conv_id = _hash_to_id(content_hash)

        # Build ORM objects
        conversation = Conversation(
            id=conv_id,
            source=parsed.source,
            external_id=parsed.external_id,
            title=parsed.title,
            created_at=parsed.created_at,
            updated_at=parsed.updated_at,
            sensitivity=SensitivityLevel.INTERNAL,
            domain_tags=None,
            message_count=0,
            hash=content_hash,
        )

        messages: list[Message] = []
        for parsed_msg in parsed.messages:
            actor = _ACTOR_MAP.get(parsed_msg.actor, ActorType.USER)

            # Encrypt content and store blob
            content_bytes = parsed_msg.content.encode("utf-8")
            blob_id = self.blob_store.store(
                content=content_bytes,
                master_key=self.master_key,
                conversation_id=conv_id,
            )

            msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                actor=actor,
                timestamp=parsed_msg.timestamp,
                content_blob_uuid=blob_id,
                sanitized_blob_uuid=None,
                sensitivity=SensitivityLevel.INTERNAL,
            )
            messages.append(msg)

        conversation.message_count = len(messages)
        conversation.messages = messages

        self.db.add_conversation(conversation)
        result.imported += 1


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _compute_conversation_hash(parsed: ParsedConversation) -> str:
    """Compute a SHA-256 content hash for a parsed conversation.

    The hash covers source, title, external_id, created_at, and a
    fingerprint of the message content so that re-imports of genuinely
    different conversations with the same title produce different hashes.

    Args:
        parsed: The ParsedConversation to fingerprint.

    Returns:
        64-character hex digest.
    """
    msg_fingerprint = "|".join(
        f"{m.actor}:{m.timestamp.isoformat()}:{m.content[:80]}"
        for m in parsed.messages
    )
    canonical = (
        f"{parsed.source}:{parsed.title}:{parsed.external_id or ''}:"
        f"{parsed.created_at.isoformat()}:{msg_fingerprint}"
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _hash_to_id(content_hash: str) -> str:
    """Convert a 64-char hex hash to a 64-char conversation primary key.

    Args:
        content_hash: 64-character SHA-256 hex digest.

    Returns:
        The same string (already a valid primary key).
    """
    return content_hash
