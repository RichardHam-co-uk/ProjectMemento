"""Python API for the ProjectMemento shared memory layer.

Provides a high-level, agent-friendly interface for storing and retrieving
memories, facts, preferences, and session context. This is the primary
entry point for agents (Claude, Codex, n8n, etc.) interacting with the
memory layer.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from memento.models import (
    Fact,
    Memory,
    MemorySensitivity,
    MemorySource,
    MemoryStatus,
    MemoryType,
    Preference,
    Session as MementoSession,
)
from memento.store import (
    DuplicateEntryError,
    EntryNotFoundError,
    SQLiteStore,
)

logger = logging.getLogger(__name__)


class MementoAPI:
    """High-level API for the ProjectMemento shared memory layer.

    This is the primary interface for agents and tools to interact with
    the memory store. It provides convenient methods for common operations
    and handles governance (staging, approval) by default.

    Example:
        >>> api = MementoAPI("vault_data/memento.db")
        >>> mem = api.remember(
        ...     title="Project decision",
        ...     summary="We chose SQLite for Phase 1 storage.",
        ...     namespace="project/myapp",
        ...     source_system="claude",
        ... )
        >>> api.approve(mem.id)
        >>> results = api.recall("SQLite storage")
    """

    def __init__(self, db_path: str | Path = "vault_data/memento.db") -> None:
        self.store = SQLiteStore(db_path)

    def close(self) -> None:
        """Close the underlying database connection."""
        self.store.close()

    def __enter__(self) -> MementoAPI:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ── Remember ───────────────────────────────────────────────────

    def remember(
        self,
        title: str,
        summary: str,
        *,
        type: MemoryType | str = MemoryType.SEMANTIC,
        namespace: str = "personal",
        sensitivity: MemorySensitivity | str = MemorySensitivity.RESTRICTED,
        body: str | None = None,
        source_system: str = "unknown",
        source_uri: str | None = None,
        confidence: float = 0.5,
        retention: str = "review",
        tags: list[str] | None = None,
        links: dict[str, list[str]] | None = None,
        created_by: str = "unknown",
        auto_approve: bool = False,
    ) -> Memory:
        """Store a new memory. Returns the created Memory object.

        The memory is staged by default. Set auto_approve=True to
        immediately approve it (use with caution).
        """
        if isinstance(type, str):
            type = MemoryType(type)
        if isinstance(sensitivity, str):
            sensitivity = MemorySensitivity(sensitivity)

        memory = Memory(
            type=type,
            namespace=namespace,
            title=title,
            summary=summary,
            body=body,
            sensitivity=sensitivity,
            source=MemorySource(system=source_system, uri=source_uri),
            confidence=confidence,
            retention=retention,
            tags=tags or [],
            links=links or {},
            created_by=created_by,
        )

        created = self.store.create_memory(memory)
        logger.info("Remembered: %s (%s)", created.id, created.title)

        if auto_approve and created.id:
            self.store.approve_memory(created.id, created_by)
            created.status = MemoryStatus.APPROVED
            created.approved_by = created_by

        return created

    def remember_fact(
        self,
        subject: str,
        predicate: str,
        object_value: str,
        *,
        namespace: str = "personal",
        source_system: str = "unknown",
        source_uri: str | None = None,
        confidence: float = 0.8,
        tags: list[str] | None = None,
    ) -> Fact:
        """Store a durable fact."""
        fact = Fact(
            subject=subject,
            predicate=predicate,
            object_value=object_value,
            namespace=namespace,
            confidence=confidence,
            source=MemorySource(system=source_system, uri=source_uri),
            tags=tags or [],
        )
        return self.store.create_fact(fact)

    def remember_preference(
        self,
        key: str,
        value: str,
        *,
        namespace: str = "personal",
        source_system: str = "unknown",
        confidence: float = 0.9,
        tags: list[str] | None = None,
    ) -> Preference:
        """Store a user/agent preference."""
        pref = Preference(
            key=key,
            value=value,
            namespace=namespace,
            confidence=confidence,
            source=MemorySource(system=source_system),
            tags=tags or [],
        )
        return self.store.create_preference(pref)

    def start_session(
        self,
        agent: str,
        title: str,
        *,
        namespace: str = "personal",
        summary: str | None = None,
        context: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> MementoSession:
        """Start a new agent session context."""
        sess = MementoSession(
            agent=agent,
            namespace=namespace,
            title=title,
            summary=summary,
            context=context or {},
            tags=tags or [],
        )
        return self.store.create_session(sess)

    # ── Recall ─────────────────────────────────────────────────────

    def recall(
        self,
        query: str,
        *,
        namespace: str | None = None,
        include_staged: bool = False,
        limit: int = 50,
    ) -> list[Memory]:
        """Search for memories by keyword. Returns approved memories by default."""
        return self.store.search_memories(
            query,
            namespace=namespace,
            include_staged=include_staged,
            limit=limit,
        )

    def get_memory(self, memory_id: str) -> Memory:
        """Retrieve a specific memory by ID."""
        return self.store.get_memory(memory_id)

    def list_memories(
        self,
        *,
        status: MemoryStatus | str | None = None,
        namespace: str | None = None,
        memory_type: MemoryType | str | None = None,
        sensitivity: MemorySensitivity | str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        """List memories with optional filters."""
        if isinstance(status, str):
            status = MemoryStatus(status)
        if isinstance(memory_type, str):
            memory_type = MemoryType(memory_type)
        if isinstance(sensitivity, str):
            sensitivity = MemorySensitivity(sensitivity)

        return self.store.list_memories(
            status=status,
            namespace=namespace,
            memory_type=memory_type,
            sensitivity=sensitivity,
            limit=limit,
            offset=offset,
        )

    def list_facts(
        self,
        *,
        namespace: str | None = None,
        status: MemoryStatus | None = None,
        limit: int = 100,
    ) -> list[Fact]:
        """List stored facts."""
        return self.store.list_facts(namespace=namespace, status=status, limit=limit)

    def list_preferences(
        self,
        *,
        namespace: str | None = None,
        status: MemoryStatus | None = None,
        limit: int = 100,
    ) -> list[Preference]:
        """List stored preferences."""
        return self.store.list_preferences(namespace=namespace, status=status, limit=limit)

    def list_sessions(
        self,
        *,
        namespace: str | None = None,
        agent: str | None = None,
        limit: int = 100,
    ) -> list[MementoSession]:
        """List agent sessions."""
        return self.store.list_sessions(namespace=namespace, agent=agent, limit=limit)

    # ── Governance ─────────────────────────────────────────────────

    def approve(self, memory_id: str, approved_by: str = "local") -> Memory:
        """Approve a staged memory so it becomes retrievable."""
        return self.store.approve_memory(memory_id, approved_by)

    def reject(self, memory_id: str, reason: str) -> Memory:
        """Reject a staged memory, keeping an audit trail."""
        return self.store.reject_memory(memory_id, reason)

    # ── Lifecycle ──────────────────────────────────────────────────

    def forget(self, memory_id: str, soft: bool = True) -> None:
        """Delete a memory. Soft delete by default."""
        self.store.delete_memory(memory_id, soft=soft)

    def end_session(self, session_id: str) -> MementoSession:
        """Mark a session as ended."""
        return self.store.end_session(session_id)

    def stats(self) -> dict[str, Any]:
        """Return store statistics."""
        return self.store.stats()
