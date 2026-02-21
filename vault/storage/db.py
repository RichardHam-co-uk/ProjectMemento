"""Database wrapper for the Vault.

Provides a clean interface for SQLite database operations via SQLAlchemy 2.x,
including session management, schema initialization, and convenience query
methods for conversations and messages.
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
    """Database wrapper class for SQLite via SQLAlchemy 2.x.

    Handles database initialization, SQLite pragma configuration,
    session management, and provides convenience methods for common
    queries.

    Attributes:
        engine: SQLAlchemy Engine instance.
        SessionLocal: Session factory bound to the engine.
    """

    def __init__(self, db_path: Path, echo: bool = False) -> None:
        """Initialize the VaultDB.

        Creates a SQLAlchemy engine with SQLite-optimized settings and
        configures pragmas for WAL mode, foreign keys, and synchronous writes.

        Args:
            db_path: Path to the SQLite database file.
            echo: If True, log all SQL queries to stdout.
        """
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=echo,
            connect_args={"check_same_thread": False},
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    def init_schema(self) -> None:
        """Create tables and run migrations.

        Applies all pending migrations to bring the database schema
        up to the latest version.
        """
        apply_migrations(self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Provide a transactional session scope.

        Commits on success, rolls back on exception, and always closes
        the session when done.

        Yields:
            A SQLAlchemy Session instance.
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
        """Get a conversation by ID.

        Args:
            conv_id: The conversation's primary key (SHA-256 hash).

        Returns:
            The Conversation object, or None if not found.
        """
        with self.get_session() as session:
            stmt = select(Conversation).where(Conversation.id == conv_id)
            return session.execute(stmt).scalar_one_or_none()

    def list_conversations(
        self,
        limit: int = 100,
        offset: int = 0,
        source: str | None = None,
    ) -> list[Conversation]:
        """List conversations with optional filtering.

        Args:
            limit: Maximum number of conversations to return.
            offset: Number of conversations to skip.
            source: If provided, filter by this source (e.g., "chatgpt").

        Returns:
            List of Conversation objects ordered by created_at descending.
        """
        with self.get_session() as session:
            stmt = select(Conversation).order_by(Conversation.created_at.desc())
            if source is not None:
                stmt = stmt.where(Conversation.source == source)
            stmt = stmt.limit(limit).offset(offset)
            return list(session.execute(stmt).scalars().all())

    def count_conversations(self) -> int:
        """Return total number of conversations.

        Returns:
            Integer count of all conversations in the database.
        """
        with self.get_session() as session:
            stmt = select(func.count()).select_from(Conversation)
            return session.execute(stmt).scalar_one()

    def count_messages(self) -> int:
        """Return total number of messages.

        Returns:
            Integer count of all messages in the database.
        """
        with self.get_session() as session:
            stmt = select(func.count()).select_from(Message)
            return session.execute(stmt).scalar_one()

    def get_messages_for_conversation(self, conv_id: str) -> list[Message]:
        """Get all messages for a conversation, ordered by timestamp.

        Args:
            conv_id: The conversation's primary key.

        Returns:
            List of Message objects sorted by timestamp ascending.
        """
        with self.get_session() as session:
            stmt = (
                select(Message)
                .where(Message.conversation_id == conv_id)
                .order_by(Message.timestamp.asc())
            )
            return list(session.execute(stmt).scalars().all())

    def add_conversation(self, conversation: Conversation) -> None:
        """Add a conversation to the database.

        Args:
            conversation: The Conversation object to persist.
        """
        with self.get_session() as session:
            session.add(conversation)

    def get_date_range(self) -> tuple[datetime | None, datetime | None]:
        """Get the oldest and newest conversation dates.

        Returns:
            Tuple of (oldest_date, newest_date). Both are None if the
            database has no conversations.
        """
        with self.get_session() as session:
            stmt = select(
                func.min(Conversation.created_at),
                func.max(Conversation.created_at),
            )
            row = session.execute(stmt).one()
            return (row[0], row[1])

    def get_source_counts(self) -> dict[str, int]:
        """Get conversation counts grouped by source.

        Returns:
            Dictionary mapping source names to their conversation counts.
            E.g., {"chatgpt": 120, "claude": 30}.
        """
        with self.get_session() as session:
            stmt = (
                select(Conversation.source, func.count())
                .group_by(Conversation.source)
            )
            rows = session.execute(stmt).all()
            return {row[0]: row[1] for row in rows}
