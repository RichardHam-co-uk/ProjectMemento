"""
Database wrapper for the Vault.

Provides a high-level interface over SQLAlchemy / SQLite with WAL mode
enabled, convenience query methods, and a transactional session context
manager.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker

from vault.storage.migrations import apply_migrations
from vault.storage.models import Conversation, Message


class VaultDB:
    """SQLite database wrapper for the LLM Memory Vault.

    Handles engine creation, SQLite pragma configuration, schema
    initialization, session management, and common query operations.

    Attributes:
        engine: SQLAlchemy engine connected to the SQLite database.
        SessionLocal: Bound sessionmaker factory.
    """

    def __init__(self, db_path: Path, echo: bool = False) -> None:
        """Initialize VaultDB and configure SQLite pragmas.

        Args:
            db_path: Path to the SQLite database file.
            echo: If True, SQLAlchemy will log all SQL statements.
        """
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=echo,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

        self.SessionLocal: sessionmaker[Session] = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def init_schema(self) -> None:
        """Create database tables and apply all pending migrations.

        Safe to call multiple times — migrations are idempotent.
        """
        apply_migrations(self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Provide a transactional database session.

        Commits on successful exit, rolls back on exception, and always
        closes the session.

        Yields:
            An active SQLAlchemy Session.

        Raises:
            Exception: Re-raises any exception after rolling back.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_conversation(self, conv_id: str) -> Conversation | None:
        """Retrieve a conversation by its primary key.

        Args:
            conv_id: The conversation ID (SHA-256 hash).

        Returns:
            The Conversation ORM object, or None if not found.
        """
        with self.get_session() as session:
            return session.get(Conversation, conv_id)

    def list_conversations(
        self,
        limit: int = 100,
        offset: int = 0,
        source: str | None = None,
    ) -> list[Conversation]:
        """List conversations with optional filtering and pagination.

        Args:
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            source: If provided, filter to conversations from this source.

        Returns:
            List of Conversation objects ordered by created_at descending.
        """
        with self.get_session() as session:
            stmt = select(Conversation).order_by(Conversation.created_at.desc())
            if source is not None:
                stmt = stmt.where(Conversation.source == source)
            stmt = stmt.limit(limit).offset(offset)
            return list(session.scalars(stmt).all())

    def count_conversations(self) -> int:
        """Return the total number of conversations in the vault.

        Returns:
            Integer count of all conversations.
        """
        with self.get_session() as session:
            result = session.execute(
                select(func.count()).select_from(Conversation)
            )
            return result.scalar_one()

    def count_messages(self) -> int:
        """Return the total number of messages in the vault.

        Returns:
            Integer count of all messages.
        """
        with self.get_session() as session:
            result = session.execute(
                select(func.count()).select_from(Message)
            )
            return result.scalar_one()

    def get_messages_for_conversation(self, conv_id: str) -> list[Message]:
        """Get all messages for a conversation ordered by timestamp.

        Args:
            conv_id: The conversation ID.

        Returns:
            List of Message objects in chronological order.
        """
        with self.get_session() as session:
            stmt = (
                select(Message)
                .where(Message.conversation_id == conv_id)
                .order_by(Message.timestamp.asc())
            )
            return list(session.scalars(stmt).all())

    def add_conversation(self, conversation: Conversation) -> None:
        """Persist a new conversation (with its messages) to the database.

        The conversation and all its related Message objects should be
        attached before calling this method.

        Args:
            conversation: The Conversation ORM object to add.
        """
        with self.get_session() as session:
            session.add(conversation)

    def conversation_hash_exists(self, hash_value: str) -> bool:
        """Check whether a conversation with the given content hash exists.

        Args:
            hash_value: The 64-character SHA-256 content hash.

        Returns:
            True if a conversation with this hash already exists.
        """
        with self.get_session() as session:
            result = session.execute(
                select(func.count()).select_from(Conversation).where(
                    Conversation.hash == hash_value
                )
            )
            return result.scalar_one() > 0

    def get_date_range(self) -> tuple[datetime | None, datetime | None]:
        """Get the date range of all conversations.

        Returns:
            Tuple of (oldest_created_at, newest_created_at). Both are None
            if the vault is empty.
        """
        with self.get_session() as session:
            result = session.execute(
                select(
                    func.min(Conversation.created_at),
                    func.max(Conversation.created_at),
                )
            )
            row = result.fetchone()
            if row is None:
                return None, None
            return row[0], row[1]

    def get_conversation_by_prefix(self, prefix: str) -> "Conversation | None":
        """Find a conversation by its full ID or a unique prefix.

        Tries an exact match first, then falls back to a LIKE prefix search.
        Returns None if no match or if the prefix is ambiguous (2+ matches).

        Args:
            prefix: Full 64-char ID or leading hex substring.

        Returns:
            The matching Conversation, or None.
        """
        with self.get_session() as session:
            exact = session.get(Conversation, prefix)
            if exact is not None:
                return exact
            stmt = (
                select(Conversation)
                .where(Conversation.id.like(f"{prefix}%"))
                .limit(2)
            )
            results = list(session.scalars(stmt).all())
            if len(results) == 1:
                return results[0]
            return None

    def get_source_counts(self) -> dict[str, int]:
        """Get conversation counts grouped by source provider.

        Returns:
            Dictionary mapping source names to their conversation counts.
            Example: {"chatgpt": 120, "claude": 30}
        """
        with self.get_session() as session:
            stmt = select(
                Conversation.source,
                func.count(Conversation.id).label("count"),
            ).group_by(Conversation.source)
            rows = session.execute(stmt).all()
            return {row[0]: row[1] for row in rows}
