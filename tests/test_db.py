"""Tests for vault.storage.db (VaultDB)."""
from pathlib import Path
from vault.storage.db import VaultDB


class TestVaultDB:
    """Test suite for VaultDB."""

    def test_placeholder(self) -> None:
        """Placeholder test — replace with real tests."""
        assert True

    def test_init_schema_creates_tables(self, tmp_path: Path) -> None:
        """init_schema() creates all required tables."""
        db = VaultDB(tmp_path / "vault.db")
        db.init_schema()
        assert db.count_conversations() == 0
        assert db.count_messages() == 0

    def test_count_conversations_empty(self, tmp_path: Path) -> None:
        """count_conversations() returns 0 on empty DB."""
        db = VaultDB(tmp_path / "vault.db")
        db.init_schema()
        assert db.count_conversations() == 0

    def test_get_source_counts_empty(self, tmp_path: Path) -> None:
        """get_source_counts() returns empty dict on empty DB."""
        db = VaultDB(tmp_path / "vault.db")
        db.init_schema()
        assert db.get_source_counts() == {}

    def test_get_date_range_empty(self, tmp_path: Path) -> None:
        """get_date_range() returns (None, None) on empty DB."""
        db = VaultDB(tmp_path / "vault.db")
        db.init_schema()
        oldest, newest = db.get_date_range()
        assert oldest is None
        assert newest is None
