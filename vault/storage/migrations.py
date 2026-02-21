"""Lightweight database schema versioning for the Vault.

Provides a simple migration system for SQLite that tracks schema versions
without the complexity of Alembic. Migrations are registered as callables
and applied in order.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import Engine, inspect, text

from vault.storage.models import Base


@dataclass
class Migration:
    """A single schema migration step.

    Attributes:
        version: Integer version number (must be unique and sequential).
        description: Human-readable description of what this migration does.
        up: Callable that applies the migration (receives an Engine).
        down: Callable that reverses the migration (receives an Engine).
    """

    version: int
    description: str
    up: Callable[[Engine], None]
    down: Callable[[Engine], None]


def _migration_1_up(engine: Engine) -> None:
    """Create all tables from ORM models."""
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO schema_version (version, applied_at, description) "
                "VALUES (:version, :applied_at, :description)"
            ),
            {
                "version": 1,
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "description": "Initial schema",
            },
        )
        conn.commit()


def _migration_1_down(engine: Engine) -> None:
    """Drop all tables from ORM models."""
    Base.metadata.drop_all(engine)


MIGRATIONS: list[Migration] = [
    Migration(
        version=1,
        description="Initial schema",
        up=_migration_1_up,
        down=_migration_1_down,
    ),
]


def _ensure_schema_version_table(engine: Engine) -> None:
    """Create the schema_version tracking table if it doesn't exist.

    This table is managed via raw SQL, not the ORM, to avoid circular
    dependencies with the migration system.

    Args:
        engine: SQLAlchemy engine instance.
    """
    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_version ("
                "    version INTEGER PRIMARY KEY,"
                "    applied_at TEXT NOT NULL,"
                "    description TEXT NOT NULL"
                ")"
            )
        )
        conn.commit()


def get_current_version(engine: Engine) -> int:
    """Get the current schema version of the database.

    Returns 0 if the schema_version table doesn't exist or contains
    no records.

    Args:
        engine: SQLAlchemy engine instance.

    Returns:
        The highest applied migration version, or 0 if none applied.
    """
    inspector = inspect(engine)
    if "schema_version" not in inspector.get_table_names():
        return 0

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT MAX(version) FROM schema_version")
        )
        row = result.scalar()
        return row if row is not None else 0


def apply_migrations(engine: Engine) -> list[int]:
    """Apply all unapplied migrations in order.

    Creates the schema_version tracking table if needed, then applies
    each migration whose version is greater than the current version.

    Args:
        engine: SQLAlchemy engine instance.

    Returns:
        List of version numbers that were applied.
    """
    _ensure_schema_version_table(engine)
    current = get_current_version(engine)
    applied: list[int] = []

    for migration in sorted(MIGRATIONS, key=lambda m: m.version):
        if migration.version > current:
            migration.up(engine)
            applied.append(migration.version)

    return applied


def needs_migration(engine: Engine) -> bool:
    """Check if there are unapplied migrations.

    Args:
        engine: SQLAlchemy engine instance.

    Returns:
        True if the current version is less than the latest migration version.
    """
    if not MIGRATIONS:
        return False
    current = get_current_version(engine)
    latest = max(m.version for m in MIGRATIONS)
    return current < latest
