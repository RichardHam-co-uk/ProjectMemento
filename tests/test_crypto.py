"""Tests for vault.security.crypto (KeyManager)."""
from vault.security.crypto import KeyManager


class TestKeyManager:
    """Test suite for KeyManager."""

    def test_placeholder(self) -> None:
        """Placeholder test — replace with real tests."""
        assert True

    def test_validate_passphrase_valid(self, tmp_vault_path, sample_passphrase) -> None:
        """Valid passphrase passes validation."""
        km = KeyManager(tmp_vault_path)
        valid, _ = km.validate_passphrase(sample_passphrase)
        assert valid is True

    def test_validate_passphrase_too_short(self, tmp_vault_path, weak_passphrase) -> None:
        """Short passphrase fails validation."""
        km = KeyManager(tmp_vault_path)
        valid, msg = km.validate_passphrase(weak_passphrase)
        assert valid is False
        assert "12" in msg

    def test_derive_master_key_returns_32_bytes(self, tmp_vault_path, sample_passphrase) -> None:
        """Derived master key is 32 bytes."""
        km = KeyManager(tmp_vault_path)
        key = km.derive_master_key(sample_passphrase)
        assert len(key) == 32

    def test_derive_master_key_deterministic(self, tmp_vault_path, sample_passphrase) -> None:
        """Same passphrase + same salt produces same key."""
        km = KeyManager(tmp_vault_path)
        key1 = km.derive_master_key(sample_passphrase)
        key2 = km.derive_master_key(sample_passphrase)
        assert key1 == key2
