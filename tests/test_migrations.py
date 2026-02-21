"""Tests for vault.storage.migrations."""
from pathlib import Path
from sqlalchemy import create_engine
from vault.storage.migrations import (
    apply_migrations,
    get_current_version,
    needs_migration,
)


class TestMigrations:
    """Test suite for the migration system."""

    def test_placeholder(self) -> None:
        """Placeholder test — replace with real tests."""
        assert True

    def test_fresh_db_version_is_zero(self, tmp_path: Path) -> None:
        """Fresh database reports version 0 before any migrations."""
        engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
        assert get_current_version(engine) == 0

    def test_apply_migrations_idempotent(self, tmp_path: Path) -> None:
        """Applying migrations twice does not raise errors."""
        engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
        apply_migrations(engine)
        apply_migrations(engine)
        assert get_current_version(engine) == 1

    def test_needs_migration_false_after_apply(self, tmp_path: Path) -> None:
        """needs_migration() returns False after all migrations are applied."""
        engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
        apply_migrations(engine)
        assert needs_migration(engine) is False

    def test_needs_migration_true_on_fresh_db(self, tmp_path: Path) -> None:
        """needs_migration() returns True on a fresh database."""
        engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
        assert needs_migration(engine) is True
