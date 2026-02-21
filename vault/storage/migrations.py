"""
Lightweight database migration system for the Vault.

Provides schema versioning without Alembic — a simple version-tracking
mechanism for SQLite using raw SQL for the version table and SQLAlchemy
ORM for the application tables.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import Engine, text

from vault.storage.models import Base


@dataclass
class Migration:
    """A single schema migration with up and down callables.

    Attributes:
        version: Integer version number (monotonically increasing).
        description: Human-readable description of the migration.
        up: Callable that applies the migration.
        down: Callable that reverses the migration.
    """

    version: int
    description: str
    up: Callable[[Engine], None]
    down: Callable[[Engine], None]


def _create_schema_version_table(engine: Engine) -> None:
    """Create the schema_version tracking table if it does not exist.

    Args:
        engine: SQLAlchemy engine to use.
    """
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL,
                    description TEXT NOT NULL
                )
                """
            )
        )
        conn.commit()


def _migration_v1_up(engine: Engine) -> None:
    """Apply migration version 1: create initial schema.

    Args:
        engine: SQLAlchemy engine.
    """
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc).isoformat()
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT OR IGNORE INTO schema_version (version, applied_at, description) "
                "VALUES (:v, :ts, :desc)"
            ),
            {"v": 1, "ts": now, "desc": "Initial schema"},
        )
        conn.commit()


def _migration_v1_down(engine: Engine) -> None:
    """Reverse migration version 1: drop all tables.

    Args:
        engine: SQLAlchemy engine.
    """
    Base.metadata.drop_all(engine)


MIGRATIONS: list[Migration] = [
    Migration(
        version=1,
        description="Initial schema",
        up=_migration_v1_up,
        down=_migration_v1_down,
    ),
]


def get_current_version(engine: Engine) -> int:
    """Get the current applied schema version.

    Returns 0 if the schema_version table does not exist or is empty.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        The highest applied migration version number, or 0 if none.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT MAX(version) FROM schema_version")
            )
            row = result.fetchone()
            if row is None or row[0] is None:
                return 0
            return int(row[0])
    except Exception:
        # Table doesn't exist yet
        return 0


def apply_migrations(engine: Engine) -> list[int]:
    """Apply all pending migrations in version order.

    Creates the schema_version table on first run, then applies each
    migration whose version is greater than the current version.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        List of version numbers that were applied.
    """
    _create_schema_version_table(engine)
    current = get_current_version(engine)
    applied: list[int] = []

    for migration in sorted(MIGRATIONS, key=lambda m: m.version):
        if migration.version > current:
            migration.up(engine)
            applied.append(migration.version)

    return applied


def needs_migration(engine: Engine) -> bool:
    """Check whether any migrations are pending.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        True if the current schema version is behind the latest migration.
    """
    if not MIGRATIONS:
        return False
    latest = max(m.version for m in MIGRATIONS)
    return get_current_version(engine) < latest
