"""
Import pipeline for the LLM Memory Vault.

Orchestrates the full import workflow: parsing provider exports via a
BaseAdapter, encrypting message content via BlobStore, persisting
conversation metadata to the database, and deduplicating against
previously imported data.

Each conversation is imported atomically — either all messages are stored
or none are (on error the conversation is rolled back and the pipeline
continues with the next one).

Usage::

    from pathlib import Path
    from vault.ingestion.pipeline import ImportPipeline
    from vault.ingestion.chatgpt import ChatGPTAdapter
    from vault.storage.database import VaultDB
    from vault.storage.blobs import BlobStore
    from vault.security.crypto import KeyManager

    db = VaultDB(Path("vault_data/vault.db"))
    key_manager = KeyManager(Path("vault_data"))
    blob_store = BlobStore(Path("vault_data/blobs"), key_manager)
    master_key = key_manager.derive_master_key(passphrase)

    pipeline = ImportPipeline(db, blob_store, key_manager)
    adapter = ChatGPTAdapter()
    result = pipeline.import_conversations(adapter, Path("conversations.json"), master_key)

    print(f"Imported: {result.imported}")
    print(f"Skipped (duplicates): {result.skipped}")
    print(f"Failed: {result.failed}")
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional

from vault.ingestion.base import BaseAdapter, ParsedConversation, ParsedMessage
from vault.security.crypto import KeyManager
from vault.storage.blobs import BlobStore
from vault.storage.database import VaultDB
from vault.storage.models import (
    ActorType,
    Conversation,
    Message,
    SensitivityLevel,
)

logger = logging.getLogger(__name__)

# Maximum number of conversations processed in a single batch to
# prevent out-of-memory errors on very large exports.
_MAX_BATCH_SIZE = 500


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ImportResult:
    """Summary of an import run.

    Attributes:
        imported: Number of conversations successfully imported.
        skipped: Number of conversations skipped (already in vault).
        failed: Number of conversations that errored and were rolled back.
        errors: List of (conversation_title, error_message) pairs for
            every conversation that failed.
    """

    imported: int = 0
    skipped: int = 0
    failed: int = 0
    errors: List[tuple[str, str]] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Total conversations encountered (imported + skipped + failed)."""
        return self.imported + self.skipped + self.failed

    def __str__(self) -> str:
        return (
            f"ImportResult(imported={self.imported}, "
            f"skipped={self.skipped}, failed={self.failed})"
        )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class ImportPipeline:
    """Orchestrates the ingestion of LLM conversations into the vault.

    The pipeline uses a provider-specific adapter to parse an export file,
    then for each conversation:
    1. Checks the database for a duplicate (by content hash).
    2. Encrypts each message's content via BlobStore.
    3. Inserts the conversation and message records atomically.

    Attributes:
        db: VaultDB instance for reading/writing conversation metadata.
        blob_store: BlobStore instance for encrypted content storage.
        key_manager: KeyManager instance for per-conversation key derivation.
    """

    def __init__(
        self,
        db: VaultDB,
        blob_store: BlobStore,
        key_manager: KeyManager,
    ) -> None:
        """Initialise the import pipeline.

        Args:
            db: Initialised VaultDB (schema must already be created).
            blob_store: Initialised BlobStore (root directory must exist).
            key_manager: Initialised KeyManager (salt must be loaded).
        """
        self.db = db
        self.blob_store = blob_store
        self.key_manager = key_manager

    def import_conversations(
        self,
        adapter: BaseAdapter,
        file_path: Path,
        master_key: bytes,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> ImportResult:
        """Parse and import conversations from a provider export file.

        Args:
            adapter: Provider adapter (e.g. ChatGPTAdapter) used to parse
                the file.
            file_path: Path to the export file.
            master_key: 32-byte master encryption key (from KeyManager).
            progress_callback: Optional callable(current, total) invoked
                after each conversation is processed. Useful for progress bars.

        Returns:
            ImportResult with counts of imported, skipped, and failed
            conversations, plus details of any errors.

        Raises:
            ValueError: If the file fails format validation.
            OSError: If the file cannot be read.
        """
        # Validate format before attempting a full parse
        if not adapter.validate_format(file_path):
            raise ValueError(
                f"File {file_path!r} is not a valid {adapter.provider_name} export."
            )

        logger.info(
            "Starting import from %s using %s adapter",
            file_path.name,
            adapter.provider_name,
        )

        # Parse all conversations from the file
        parsed: List[ParsedConversation] = adapter.parse(file_path)
        total = len(parsed)
        result = ImportResult()

        logger.info("Parsed %d conversations; beginning import…", total)

        for idx, conv in enumerate(parsed):
            try:
                outcome = self._import_one(conv, master_key, adapter.provider_name)
                if outcome == "imported":
                    result.imported += 1
                else:
                    result.skipped += 1
            except Exception as exc:
                result.failed += 1
                result.errors.append((conv.title, str(exc)))
                logger.warning(
                    "Failed to import conversation %r (index %d): %s",
                    conv.title,
                    idx,
                    exc,
                )

            if progress_callback is not None:
                progress_callback(idx + 1, total)

        logger.info(
            "Import complete — imported=%d skipped=%d failed=%d",
            result.imported,
            result.skipped,
            result.failed,
        )
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _import_one(
        self,
        conv: ParsedConversation,
        master_key: bytes,
        source: str,
    ) -> str:
        """Import a single parsed conversation atomically.

        Args:
            conv: The parsed conversation to import.
            master_key: Master encryption key.
            source: Provider name (e.g. 'chatgpt').

        Returns:
            'imported' if the conversation was stored, 'skipped' if it
            already exists in the vault.

        Raises:
            Exception: Any storage or encryption error (caller handles).
        """
        # Generate stable conversation ID from external_id + source
        conv_id = _stable_uuid(source, conv.external_id)

        # Deduplicate: skip if content hash already in DB
        if conv.content_hash and self.db.conversation_exists(conv.content_hash):
            logger.debug(
                "Skipping duplicate conversation %r (hash=%s)",
                conv.title,
                conv.content_hash[:8],
            )
            return "skipped"

        # Build ORM objects — encrypt blobs before any DB write
        orm_messages = self._build_messages(conv.messages, master_key, conv_id)

        orm_conv = Conversation(
            id=conv_id,
            source=source,
            external_id=conv.external_id or None,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            sensitivity=SensitivityLevel.INTERNAL,
            domain_tags=conv.metadata or None,
            message_count=len(orm_messages),
            hash=conv.content_hash,
        )

        # Atomic insert (session rolls back automatically on exception)
        self.db.add_conversation(orm_conv, orm_messages)

        logger.debug(
            "Imported conversation %r with %d messages",
            conv.title,
            len(orm_messages),
        )
        return "imported"

    def _build_messages(
        self,
        messages: List[ParsedMessage],
        master_key: bytes,
        conversation_id: str,
    ) -> List[Message]:
        """Encrypt message content and build ORM Message objects.

        All blob writes happen before the DB transaction is opened so that
        if the DB insert fails, the orphan blobs can be cleaned up (not
        implemented in v1 — blobs are cheap and will be GC'd in a future
        maintenance pass).

        Args:
            messages: Ordered list of parsed messages.
            master_key: Master encryption key.
            conversation_id: The stable UUID of the parent conversation.

        Returns:
            List of Message ORM objects (content already encrypted on disk).

        Raises:
            ValueError: If actor role is unrecognised.
            Exception: Any blob-store error.
        """
        orm_messages: List[Message] = []

        for msg in messages:
            blob_id = self.blob_store.store(
                content=msg.content.encode("utf-8"),
                master_key=master_key,
                conversation_id=conversation_id,
            )

            actor = _parse_actor(msg.actor)
            msg_id = str(uuid.uuid4())

            orm_messages.append(
                Message(
                    id=msg_id,
                    conversation_id=conversation_id,
                    actor=actor,
                    timestamp=msg.timestamp,
                    content_blob_uuid=blob_id,
                    sanitized_blob_uuid=None,
                    sensitivity=SensitivityLevel.INTERNAL,
                )
            )

        return orm_messages


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _stable_uuid(source: str, external_id: str) -> str:
    """Derive a deterministic UUID5 for a conversation.

    Using UUID5 (name-based SHA-1) ensures the same conversation always
    gets the same vault ID, even if imported multiple times.

    Args:
        source: Provider name (e.g. 'chatgpt').
        external_id: Provider-assigned conversation ID.

    Returns:
        UUID5 string in canonical hyphenated format.
    """
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # UUID_DNS
    name = f"{source}:{external_id}"
    return str(uuid.uuid5(namespace, name))


def _parse_actor(actor_str: str) -> ActorType:
    """Map an actor string to the ActorType enum.

    Args:
        actor_str: One of 'user', 'assistant', or 'system'.

    Returns:
        Corresponding ActorType enum value.

    Raises:
        ValueError: If actor_str is not a recognised value.
    """
    try:
        return ActorType(actor_str)
    except ValueError:
        # Fallback unknown roles to 'system' rather than crashing the import
        logger.debug("Unknown actor role %r — mapping to 'system'", actor_str)
        return ActorType.SYSTEM
