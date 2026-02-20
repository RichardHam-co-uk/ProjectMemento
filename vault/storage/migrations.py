"""Lightweight database migration system for the LLM Memory Vault.

This module provides a simple schema versioning mechanism for SQLite.
It intentionally avoids Alembic in favour of a minimal, transparent
approach: each migration is a plain Python callable that receives an
SQLAlchemy Engine and performs its changes directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, List

from sqlalchemy import Engine, text

from vault.storage.models import Base


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class Migration:
    """A single, versioned database migration.

    Args:
        version: Monotonically increasing integer that identifies this
            migration.  Must be unique across all migrations.
        description: Human-readable summary of what the migration does.
        up: Callable that applies the migration to the database.
        down: Callable that reverts the migration from the database.
    """

    version: int
    description: str
    up: Callable[[Engine], None]
    down: Callable[[Engine], None]


# ---------------------------------------------------------------------------
# Migration implementations
# ---------------------------------------------------------------------------


def _v1_up(engine: Engine) -> None:
    """Apply version 1: create the initial schema.

    Args:
        engine: SQLAlchemy engine connected to the target database.
    """
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
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


def _v1_down(engine: Engine) -> None:
    """Revert version 1: drop all ORM-managed tables.

    Args:
        engine: SQLAlchemy engine connected to the target database.
    """
    Base.metadata.drop_all(engine)


# ---------------------------------------------------------------------------
# Migration registry
# ---------------------------------------------------------------------------

MIGRATIONS: List[Migration] = [
    Migration(
        version=1,
        description="Initial schema",
        up=_v1_up,
        down=_v1_down,
    ),
]

# ---------------------------------------------------------------------------
# Helper: schema_version table bootstrap
# ---------------------------------------------------------------------------


def _ensure_version_table(engine: Engine) -> None:
    """Create the schema_version table if it does not already exist.

    The table is created with raw SQL rather than the ORM so that it is
    always available, even before the first migration has run.

    Args:
        engine: SQLAlchemy engine connected to the target database.
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_version ("
                "    version     INTEGER PRIMARY KEY, "
                "    applied_at  TEXT    NOT NULL, "
                "    description TEXT    NOT NULL"
                ")"
            )
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_current_version(engine: Engine) -> int:
    """Return the highest migration version that has been applied.

    Returns 0 when the schema_version table does not yet exist or when no
    migrations have been recorded (i.e. a completely fresh database).

    Args:
        engine: SQLAlchemy engine connected to the target database.

    Returns:
        The current schema version as an integer (0 if none applied).
    """
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT MAX(version) FROM schema_version")
            ).fetchone()
            return int(row[0]) if row and row[0] is not None else 0
    except Exception:
        # Table does not exist yet.
        return 0


def needs_migration(engine: Engine) -> bool:
    """Return True when there are unapplied migrations waiting to run.

    Args:
        engine: SQLAlchemy engine connected to the target database.

    Returns:
        True if the current schema version is behind the latest migration
        version, False otherwise.
    """
    if not MIGRATIONS:
        return False
    latest = max(m.version for m in MIGRATIONS)
    return get_current_version(engine) < latest


def apply_migrations(engine: Engine) -> List[int]:
    """Apply all unapplied migrations in ascending version order.

    The schema_version table is created automatically if it does not exist.
    Migrations that have already been applied are skipped silently, making
    this function safe to call multiple times (idempotent).

    Args:
        engine: SQLAlchemy engine connected to the target database.

    Returns:
        A list of version numbers for each migration that was applied during
        this call.  An empty list indicates that the database was already
        up-to-date.
    """
    _ensure_version_table(engine)
    current = get_current_version(engine)
    applied: List[int] = []

    for migration in sorted(MIGRATIONS, key=lambda m: m.version):
        if migration.version > current:
            migration.up(engine)
            applied.append(migration.version)
            current = migration.version

    return applied
