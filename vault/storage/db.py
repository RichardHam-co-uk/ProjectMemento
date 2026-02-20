"""Database wrapper for the LLM Memory Vault.

Provides :class:`VaultDB`, a thin SQLAlchemy 2.x wrapper around SQLite that
handles engine creation, SQLite pragma configuration, schema initialisation via
the migration system, session management, and common convenience queries.
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
    """SQLite database wrapper using SQLAlchemy 2.x.

    Encapsulates engine creation, SQLite pragma setup, schema initialisation,
    transactional session management, and common read/write convenience methods.

    Args:
        db_path: Filesystem path to the SQLite database file.  The parent
            directory must already exist.
        echo: When True, SQLAlchemy will log all SQL statements to stdout.
            Useful for debugging.  Defaults to False.

    Example:
        >>> db = VaultDB(Path("/var/vault/vault.db"))
        >>> db.init_schema()
        >>> with db.get_session() as session:
        ...     session.add(some_conversation)
    """

    def __init__(self, db_path: Path, echo: bool = False) -> None:
        self.db_path = db_path
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=echo,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

        self.SessionLocal: sessionmaker[Session] = sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False
        )

    # ------------------------------------------------------------------
    # Schema initialisation
    # ------------------------------------------------------------------

    def init_schema(self) -> None:
        """Create all tables and apply pending migrations.

        Safe to call multiple times — :func:`apply_migrations` is idempotent.
        """
        apply_migrations(self.engine)

    # ------------------------------------------------------------------
    # Session context manager
    # ------------------------------------------------------------------

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Provide a transactional database session.

        Commits on clean exit, rolls back on any exception, and always closes
        the underlying connection.

        Yields:
            An open :class:`~sqlalchemy.orm.Session` instance.

        Raises:
            Exception: Re-raises any exception that occurs within the block
                after rolling back the transaction.

        Example:
            >>> with db.get_session() as session:
            ...     session.add(new_conversation)
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

    # ------------------------------------------------------------------
    # Conversation queries
    # ------------------------------------------------------------------

    def get_conversation(self, conv_id: str) -> Conversation | None:
        """Retrieve a single conversation by its primary-key ID.

        Args:
            conv_id: The 64-character SHA-256 conversation identifier.

        Returns:
            The matching :class:`~vault.storage.models.Conversation` instance,
            or None if no record exists with that ID.
        """
        with self.get_session() as session:
            return session.get(Conversation, conv_id)

    def list_conversations(
        self,
        limit: int = 100,
        offset: int = 0,
        source: str | None = None,
    ) -> list[Conversation]:
        """Return a paginated list of conversations, newest first.

        Args:
            limit: Maximum number of records to return.  Defaults to 100.
            offset: Number of records to skip before returning results.
                Defaults to 0.
            source: When provided, only conversations whose ``source`` field
                matches this value are returned (e.g. ``"chatgpt"``).

        Returns:
            A list of :class:`~vault.storage.models.Conversation` instances
            ordered by ``created_at`` descending.
        """
        with self.get_session() as session:
            stmt = select(Conversation).order_by(Conversation.created_at.desc())
            if source is not None:
                stmt = stmt.where(Conversation.source == source)
            stmt = stmt.limit(limit).offset(offset)
            return list(session.scalars(stmt).all())

    def count_conversations(self) -> int:
        """Return the total number of conversations stored in the vault.

        Returns:
            Integer count of all rows in the ``conversations`` table.
        """
        with self.get_session() as session:
            result = session.execute(
                select(func.count()).select_from(Conversation)
            ).scalar_one()
            return int(result)

    def count_messages(self) -> int:
        """Return the total number of messages stored in the vault.

        Returns:
            Integer count of all rows in the ``messages`` table.
        """
        with self.get_session() as session:
            result = session.execute(
                select(func.count()).select_from(Message)
            ).scalar_one()
            return int(result)

    def get_messages_for_conversation(self, conv_id: str) -> list[Message]:
        """Return all messages for a conversation in chronological order.

        Args:
            conv_id: The 64-character SHA-256 conversation identifier.

        Returns:
            A list of :class:`~vault.storage.models.Message` instances ordered
            by ``timestamp`` ascending.  Returns an empty list if the
            conversation does not exist or has no messages.
        """
        with self.get_session() as session:
            stmt = (
                select(Message)
                .where(Message.conversation_id == conv_id)
                .order_by(Message.timestamp.asc())
            )
            return list(session.scalars(stmt).all())

    def add_conversation(self, conversation: Conversation) -> None:
        """Persist a new conversation (and its related objects) to the database.

        The ``conversation`` object may carry pre-populated ``messages`` and
        ``artifacts`` relationships; SQLAlchemy's cascade rules will insert
        them automatically.

        Args:
            conversation: A fully-populated
                :class:`~vault.storage.models.Conversation` instance that has
                not yet been added to any session.
        """
        with self.get_session() as session:
            session.add(conversation)

    # ------------------------------------------------------------------
    # Aggregate / stats queries
    # ------------------------------------------------------------------

    def get_date_range(self) -> tuple[datetime | None, datetime | None]:
        """Return the earliest and latest conversation creation timestamps.

        Returns:
            A two-tuple ``(oldest, newest)`` where each element is either a
            :class:`~datetime.datetime` or ``None`` if the vault contains no
            conversations.
        """
        with self.get_session() as session:
            row = session.execute(
                select(
                    func.min(Conversation.created_at),
                    func.max(Conversation.created_at),
                )
            ).one()
            return (row[0], row[1])

    def get_source_counts(self) -> dict[str, int]:
        """Return conversation counts grouped by provider source.

        Returns:
            A dictionary mapping each distinct ``source`` value to its
            conversation count, for example
            ``{"chatgpt": 120, "claude": 30}``.
        """
        with self.get_session() as session:
            rows = session.execute(
                select(Conversation.source, func.count(Conversation.id)).group_by(
                    Conversation.source
                )
            ).all()
            return {row[0]: int(row[1]) for row in rows}
