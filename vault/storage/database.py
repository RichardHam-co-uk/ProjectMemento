"""
SQLite database wrapper for the Vault.

Provides a thin layer around SQLAlchemy to manage the vault database,
enforcing WAL mode, foreign keys, and offering convenience helpers for
the models defined in vault.storage.models.

Note: Task 1.4.1 (Tier 2) owns this file. This implementation is the
minimal functional version; the Tier 2 task should extend it with
migration support and any additional query helpers needed.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional

import sqlalchemy as sa
from sqlalchemy import create_engine, exists, select
from sqlalchemy.orm import Session, sessionmaker

from vault.storage.models import Base, Conversation, Message


class VaultDB:
    """SQLAlchemy-backed database wrapper for the Vault.

    Manages a SQLite database with WAL journaling and foreign key
    enforcement. All transactional work is done via the session()
    context manager which auto-commits on success and rolls back on error.

    Attributes:
        db_path: Filesystem path to the SQLite database file.
    """

    def __init__(self, db_path: Path, echo: bool = False) -> None:
        """Initialize the database wrapper.

        Args:
            db_path: Path to the SQLite .db file. Parent directories
                are created automatically.
            echo: If True, SQLAlchemy logs all SQL statements (dev only).
        """
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._engine = create_engine(
            f"sqlite:///{db_path}",
            echo=echo,
            connect_args={"check_same_thread": False},
        )

        # Apply pragmas on every new connection via an event listener
        @sa.event.listens_for(self._engine, "connect")
        def _set_pragmas(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        self._Session = sessionmaker(bind=self._engine, expire_on_commit=False)

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------

    def create_schema(self) -> None:
        """Create all ORM-mapped tables if they do not already exist."""
        Base.metadata.create_all(self._engine)

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Provide a transactional database session.

        Automatically commits on clean exit and rolls back on exception.

        Yields:
            An open SQLAlchemy Session.

        Raises:
            Any exception raised inside the block (after rollback).
        """
        s = self._Session()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def conversation_exists(self, content_hash: str) -> bool:
        """Check whether a conversation with the given hash is stored.

        Args:
            content_hash: SHA-256 hex digest of the conversation content.

        Returns:
            True if a conversation with this hash already exists.
        """
        with self.session() as s:
            return s.scalar(
                select(exists().where(Conversation.hash == content_hash))
            )

    def add_conversation(
        self,
        conversation: Conversation,
        messages: List[Message],
    ) -> None:
        """Persist a conversation and all its messages atomically.

        Args:
            conversation: The Conversation ORM object to insert.
            messages: List of Message ORM objects belonging to the conversation.

        Raises:
            sqlalchemy.exc.IntegrityError: If the conversation hash already exists.
        """
        with self.session() as s:
            s.add(conversation)
            for message in messages:
                s.add(message)

    def get_conversation_count(self) -> int:
        """Return the total number of conversations stored.

        Returns:
            Count of rows in the conversations table.
        """
        with self.session() as s:
            return s.scalar(select(sa.func.count()).select_from(Conversation)) or 0

    def get_message_count(self) -> int:
        """Return the total number of messages stored.

        Returns:
            Count of rows in the messages table.
        """
        with self.session() as s:
            return s.scalar(select(sa.func.count()).select_from(Message)) or 0
