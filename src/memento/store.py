"""SQLite backend for the ProjectMemento shared memory layer.

Provides CRUD operations for Memory, Fact, Preference, and Session entities
using SQLAlchemy 2.0 with a file-based SQLite database.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    event,
    text as sa_text,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

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

logger = logging.getLogger(__name__)

Base = declarative_base()


class MemoryRecord(Base):
    """SQLAlchemy ORM model for memory records."""

    __tablename__ = "memories"

    id = Column(String, primary_key=True)
    entity_type = Column(String, nullable=False, default="memory")  # memory, fact, preference, session
    memory_type = Column(String, nullable=True)  # episodic, semantic, etc.
    namespace = Column(String, nullable=False, default="personal")
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    sensitivity = Column(String, nullable=False, default="restricted")
    status = Column(String, nullable=False, default="staged")
    confidence = Column(Float, nullable=False, default=0.5)
    retention = Column(String, nullable=True, default="review")
    source_system = Column(String, nullable=True)
    source_uri = Column(String, nullable=True)
    created_by = Column(String, nullable=True, default="unknown")
    approved_by = Column(String, nullable=True)
    status_reason = Column(Text, nullable=True)
    tags = Column(Text, nullable=True, default="[]")  # JSON array
    links = Column(Text, nullable=True, default="{}")  # JSON object
    content_hash = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    # Extra fields for non-memory entities
    # Facts: subject, predicate, object_value
    subject = Column(String, nullable=True)
    predicate = Column(String, nullable=True)
    object_value = Column(Text, nullable=True)
    # Preferences: key, value
    key = Column(String, nullable=True)
    value = Column(Text, nullable=True)
    # Sessions: agent, context
    agent = Column(String, nullable=True)
    context_json = Column(Text, nullable=True, default="{}")

    # Soft delete
    is_deleted = Column(Boolean, nullable=False, default=False)


class DuplicateEntryError(ValueError):
    """Raised when a deterministic content hash already exists in the store."""


class EntryNotFoundError(KeyError):
    """Raised when a requested entry ID is absent."""


class SQLiteStore:
    """SQLite-backed memory store with CRUD operations.

    Manages the full lifecycle of memory records, facts, preferences,
    and sessions in a single unified table with entity-type discrimination.
    """

    def __init__(self, db_path: str | Path = "vault_data/memento.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        # Enable WAL mode for better concurrent read performance
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info("SQLiteStore initialized at %s", self.db_path)

    def close(self) -> None:
        """Dispose of the database engine."""
        self.engine.dispose()

    # ── Memory CRUD ────────────────────────────────────────────────

    def create_memory(self, memory: Memory) -> Memory:
        """Store a new memory record. Raises DuplicateEntryError if hash exists."""
        memory.content_hash = memory.compute_content_hash()
        memory.id = memory.deterministic_id()

        with self.Session() as session:
            existing = session.get(MemoryRecord, memory.id)
            if existing is not None:
                raise DuplicateEntryError(f"memory already exists: {memory.id}")

            record = self._memory_to_record(memory)
            session.add(record)
            session.commit()
            logger.debug("Created memory %s", memory.id)
            return memory

    def get_memory(self, memory_id: str) -> Memory:
        """Retrieve a memory by ID. Raises EntryNotFoundError if absent."""
        with self.Session() as session:
            record = session.get(MemoryRecord, memory_id)
            if record is None or record.is_deleted:
                raise EntryNotFoundError(memory_id)
            return self._record_to_memory(record)

    def update_memory(self, memory_id: str, **updates: Any) -> Memory:
        """Update fields on an existing memory record."""
        with self.Session() as session:
            record = session.get(MemoryRecord, memory_id)
            if record is None or record.is_deleted:
                raise EntryNotFoundError(memory_id)

            for key, value in updates.items():
                if hasattr(record, key):
                    setattr(record, key, value)

            record.updated_at = datetime.now(timezone.utc)
            # Recompute content hash if core fields changed
            memory = self._record_to_memory(record)
            record.content_hash = memory.compute_content_hash()
            record.id = memory.deterministic_id()

            session.commit()
            return self._record_to_memory(record)

    def delete_memory(self, memory_id: str, soft: bool = True) -> None:
        """Delete a memory. Soft delete by default (sets is_deleted flag)."""
        with self.Session() as session:
            record = session.get(MemoryRecord, memory_id)
            if record is None:
                raise EntryNotFoundError(memory_id)
            if soft:
                record.is_deleted = True
                record.updated_at = datetime.now(timezone.utc)
            else:
                session.delete(record)
            session.commit()

    def list_memories(
        self,
        *,
        status: MemoryStatus | None = None,
        namespace: str | None = None,
        memory_type: MemoryType | None = None,
        sensitivity: MemorySensitivity | None = None,
        query: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        """List memories with optional filters."""
        with self.Session() as session:
            q = session.query(MemoryRecord).filter(
                MemoryRecord.entity_type == "memory"
            )
            if not include_deleted:
                q = q.filter(MemoryRecord.is_deleted == False)
            if status is not None:
                q = q.filter(MemoryRecord.status == status.value)
            if namespace is not None:
                q = q.filter(MemoryRecord.namespace == namespace)
            if memory_type is not None:
                q = q.filter(MemoryRecord.memory_type == memory_type.value)
            if sensitivity is not None:
                q = q.filter(MemoryRecord.sensitivity == sensitivity.value)
            if query:
                needle = f"%{query.lower()}%"
                q = q.filter(
                    sa_text(
                        "LOWER(memories.title || ' ' || COALESCE(memories.summary, '') || ' ' || COALESCE(memories.body, '')) LIKE :needle"
                    ).params(needle=needle)
                )

            records = q.order_by(MemoryRecord.created_at.desc()).offset(offset).limit(limit).all()
            return [self._record_to_memory(r) for r in records]

    def approve_memory(self, memory_id: str, approved_by: str = "local") -> Memory:
        """Approve a staged memory so it becomes retrievable."""
        return self.update_memory(
            memory_id,
            status=MemoryStatus.APPROVED.value,
            approved_by=approved_by,
        )

    def reject_memory(self, memory_id: str, reason: str) -> Memory:
        """Reject a staged memory, keeping an audit trail."""
        return self.update_memory(
            memory_id,
            status=MemoryStatus.REJECTED.value,
            status_reason=reason,
        )

    def search_memories(
        self,
        query: str,
        *,
        namespace: str | None = None,
        include_staged: bool = False,
        limit: int = 50,
    ) -> list[Memory]:
        """Keyword search over titles, summaries, and bodies.

        Retrieval is governed: approved records only unless include_staged=True.
        """
        status = None if include_staged else MemoryStatus.APPROVED
        return self.list_memories(
            status=status,
            namespace=namespace,
            query=query,
            limit=limit,
        )

    # ── Fact CRUD ──────────────────────────────────────────────────

    def create_fact(self, fact: Fact) -> Fact:
        """Store a new fact."""
        fact.content_hash = fact.compute_content_hash()
        fact.id = fact.deterministic_id()

        with self.Session() as session:
            existing = session.get(MemoryRecord, fact.id)
            if existing is not None:
                raise DuplicateEntryError(f"fact already exists: {fact.id}")

            record = self._fact_to_record(fact)
            session.add(record)
            session.commit()
            return fact

    def get_fact(self, fact_id: str) -> Fact:
        with self.Session() as session:
            record = session.get(MemoryRecord, fact_id)
            if record is None or record.is_deleted:
                raise EntryNotFoundError(fact_id)
            return self._record_to_fact(record)

    def list_facts(
        self,
        *,
        namespace: str | None = None,
        status: MemoryStatus | None = None,
        limit: int = 100,
    ) -> list[Fact]:
        with self.Session() as session:
            q = session.query(MemoryRecord).filter(
                MemoryRecord.entity_type == "fact",
                MemoryRecord.is_deleted == False,
            )
            if namespace:
                q = q.filter(MemoryRecord.namespace == namespace)
            if status:
                q = q.filter(MemoryRecord.status == status.value)
            records = q.order_by(MemoryRecord.created_at.desc()).limit(limit).all()
            return [self._record_to_fact(r) for r in records]

    # ── Preference CRUD ────────────────────────────────────────────

    def create_preference(self, pref: Preference) -> Preference:
        pref.content_hash = pref.compute_content_hash()
        pref.id = pref.deterministic_id()

        with self.Session() as session:
            existing = session.get(MemoryRecord, pref.id)
            if existing is not None:
                raise DuplicateEntryError(f"preference already exists: {pref.id}")

            record = self._preference_to_record(pref)
            session.add(record)
            session.commit()
            return pref

    def get_preference(self, pref_id: str) -> Preference:
        with self.Session() as session:
            record = session.get(MemoryRecord, pref_id)
            if record is None or record.is_deleted:
                raise EntryNotFoundError(pref_id)
            return self._record_to_preference(record)

    def list_preferences(
        self,
        *,
        namespace: str | None = None,
        status: MemoryStatus | None = None,
        limit: int = 100,
    ) -> list[Preference]:
        with self.Session() as session:
            q = session.query(MemoryRecord).filter(
                MemoryRecord.entity_type == "preference",
                MemoryRecord.is_deleted == False,
            )
            if namespace:
                q = q.filter(MemoryRecord.namespace == namespace)
            if status:
                q = q.filter(MemoryRecord.status == status.value)
            records = q.order_by(MemoryRecord.created_at.desc()).limit(limit).all()
            return [self._record_to_preference(r) for r in records]

    # ── Session CRUD ───────────────────────────────────────────────

    def create_session(self, sess: MementoSession) -> MementoSession:
        sess.content_hash = sess.compute_content_hash()
        sess.id = sess.deterministic_id()

        with self.Session() as session:
            existing = session.get(MemoryRecord, sess.id)
            if existing is not None:
                raise DuplicateEntryError(f"session already exists: {sess.id}")

            record = self._session_to_record(sess)
            session.add(record)
            session.commit()
            return sess

    def get_session(self, session_id: str) -> MementoSession:
        with self.Session() as session:
            record = session.get(MemoryRecord, session_id)
            if record is None or record.is_deleted:
                raise EntryNotFoundError(session_id)
            return self._record_to_session(record)

    def list_sessions(
        self,
        *,
        namespace: str | None = None,
        agent: str | None = None,
        limit: int = 100,
    ) -> list[MementoSession]:
        with self.Session() as session:
            q = session.query(MemoryRecord).filter(
                MemoryRecord.entity_type == "session",
                MemoryRecord.is_deleted == False,
            )
            if namespace:
                q = q.filter(MemoryRecord.namespace == namespace)
            if agent:
                q = q.filter(MemoryRecord.agent == agent)
            records = q.order_by(MemoryRecord.created_at.desc()).limit(limit).all()
            return [self._record_to_session(r) for r in records]

    def end_session(self, session_id: str) -> MementoSession:
        return self._update_session_raw(
            session_id,
            ended_at=datetime.now(timezone.utc),
        )

    # ── Stats ──────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Return basic statistics about the store."""
        with self.Session() as session:
            total = session.query(MemoryRecord).filter(
                MemoryRecord.is_deleted == False
            ).count()
            by_status = {}
            for status in MemoryStatus:
                count = session.query(MemoryRecord).filter(
                    MemoryRecord.status == status.value,
                    MemoryRecord.is_deleted == False,
                ).count()
                by_status[status.value] = count
            by_type = {}
            for mtype in MemoryType:
                count = session.query(MemoryRecord).filter(
                    MemoryRecord.memory_type == mtype.value,
                    MemoryRecord.is_deleted == False,
                ).count()
                by_type[mtype.value] = count
            return {
                "total_records": total,
                "by_status": by_status,
                "by_type": by_type,
                "db_path": str(self.db_path),
                "db_size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0,
            }

    # ── Conversion helpers ─────────────────────────────────────────

    @staticmethod
    def _memory_to_record(m: Memory) -> MemoryRecord:
        return MemoryRecord(
            id=m.id or m.deterministic_id(),
            entity_type="memory",
            memory_type=m.type.value if isinstance(m.type, MemoryType) else m.type,
            namespace=m.namespace,
            title=m.title,
            summary=m.summary,
            body=m.body,
            sensitivity=m.sensitivity.value if isinstance(m.sensitivity, MemorySensitivity) else m.sensitivity,
            status=m.status.value if isinstance(m.status, MemoryStatus) else m.status,
            confidence=m.confidence,
            retention=m.retention,
            source_system=m.source.system if m.source else None,
            source_uri=m.source.uri if m.source else None,
            created_by=m.created_by,
            approved_by=m.approved_by,
            status_reason=m.status_reason,
            tags=json.dumps(m.tags),
            links=json.dumps(m.links),
            content_hash=m.content_hash or m.compute_content_hash(),
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    @staticmethod
    def _record_to_memory(r: MemoryRecord) -> Memory:
        return Memory(
            id=r.id,
            type=MemoryType(r.memory_type) if r.memory_type else MemoryType.SEMANTIC,
            namespace=r.namespace,
            title=r.title,
            summary=r.summary or "",
            body=r.body,
            sensitivity=MemorySensitivity(r.sensitivity),
            status=MemoryStatus(r.status),
            confidence=r.confidence,
            retention=r.retention or "review",
            source=MemorySource(
                system=r.source_system or "unknown",
                uri=r.source_uri,
            ),
            created_by=r.created_by or "unknown",
            approved_by=r.approved_by,
            status_reason=r.status_reason,
            tags=json.loads(r.tags) if r.tags else [],
            links=json.loads(r.links) if r.links else {},
            content_hash=r.content_hash,
            created_at=r.created_at,
            updated_at=r.updated_at or r.created_at,
        )

    @staticmethod
    def _fact_to_record(f: Fact) -> MemoryRecord:
        return MemoryRecord(
            id=f.id or f.deterministic_id(),
            entity_type="fact",
            namespace=f.namespace,
            title=f"{f.subject} {f.predicate} {f.object_value}"[:200],
            summary=f"{f.predicate} {f.object_value}",
            confidence=f.confidence,
            source_system=f.source.system if f.source else None,
            source_uri=f.source.uri if f.source else None,
            status=f.status.value if isinstance(f.status, MemoryStatus) else f.status,
            tags=json.dumps(f.tags),
            content_hash=f.content_hash or f.compute_content_hash(),
            created_at=f.created_at,
            updated_at=f.updated_at,
            subject=f.subject,
            predicate=f.predicate,
            object_value=f.object_value,
        )

    @staticmethod
    def _record_to_fact(r: MemoryRecord) -> Fact:
        return Fact(
            id=r.id,
            subject=r.subject or "",
            predicate=r.predicate or "",
            object_value=r.object_value or "",
            namespace=r.namespace,
            confidence=r.confidence,
            source=MemorySource(
                system=r.source_system or "unknown",
                uri=r.source_uri,
            ),
            status=MemoryStatus(r.status),
            tags=json.loads(r.tags) if r.tags else [],
            content_hash=r.content_hash,
            created_at=r.created_at,
            updated_at=r.updated_at or r.created_at,
        )

    @staticmethod
    def _preference_to_record(p: Preference) -> MemoryRecord:
        return MemoryRecord(
            id=p.id or p.deterministic_id(),
            entity_type="preference",
            namespace=p.namespace,
            title=f"{p.key}: {p.value}"[:200],
            summary=p.value,
            confidence=p.confidence,
            source_system=p.source.system if p.source else None,
            source_uri=p.source.uri if p.source else None,
            status=p.status.value if isinstance(p.status, MemoryStatus) else p.status,
            tags=json.dumps(p.tags),
            content_hash=p.content_hash or p.compute_content_hash(),
            created_at=p.created_at,
            updated_at=p.updated_at,
            key=p.key,
            value=p.value,
        )

    @staticmethod
    def _record_to_preference(r: MemoryRecord) -> Preference:
        return Preference(
            id=r.id,
            key=r.key or "",
            value=r.value or "",
            namespace=r.namespace,
            confidence=r.confidence,
            source=MemorySource(
                system=r.source_system or "unknown",
                uri=r.source_uri,
            ),
            status=MemoryStatus(r.status),
            tags=json.loads(r.tags) if r.tags else [],
            content_hash=r.content_hash,
            created_at=r.created_at,
            updated_at=r.updated_at or r.created_at,
        )

    @staticmethod
    def _session_to_record(s: MementoSession) -> MemoryRecord:
        return MemoryRecord(
            id=s.id or s.deterministic_id(),
            entity_type="session",
            namespace=s.namespace,
            title=s.title,
            summary=s.summary,
            status=MemoryStatus.APPROVED.value,
            tags=json.dumps(s.tags),
            content_hash=s.content_hash or s.compute_content_hash(),
            created_at=s.created_at,
            updated_at=s.updated_at,
            ended_at=s.ended_at,
            agent=s.agent,
            context_json=json.dumps(s.context),
        )

    @staticmethod
    def _record_to_session(r: MemoryRecord) -> MementoSession:
        return MementoSession(
            id=r.id,
            agent=r.agent or "",
            namespace=r.namespace,
            title=r.title,
            summary=r.summary,
            context=json.loads(r.context_json) if r.context_json else {},
            tags=json.loads(r.tags) if r.tags else [],
            content_hash=r.content_hash,
            created_at=r.created_at,
            updated_at=r.updated_at or r.created_at,
            ended_at=r.ended_at,
        )

    def _update_session_raw(self, session_id: str, **kwargs: Any) -> MementoSession:
        with self.Session() as session:
            record = session.get(MemoryRecord, session_id)
            if record is None or record.is_deleted:
                raise EntryNotFoundError(session_id)
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            record.updated_at = datetime.now(timezone.utc)
            session.commit()
            return self._record_to_session(record)
