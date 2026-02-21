"""Tests for vault.security.session (SessionManager)."""
from vault.security.session import SessionManager
from vault.security.crypto import KeyManager


class TestSessionManager:
    """Test suite for SessionManager."""

    def test_placeholder(self) -> None:
        """Placeholder test — replace with real tests."""
        assert True

    def test_create_and_validate_session(self, tmp_vault_path, sample_passphrase) -> None:
        """A created session token validates and returns the master key."""
        km = KeyManager(tmp_vault_path)
        master_key = km.derive_master_key(sample_passphrase)
        sm = SessionManager(tmp_vault_path)
        token = sm.create_session(master_key)
        recovered = sm.validate_token(token)
        assert recovered == master_key

    def test_invalid_token_returns_none(self, tmp_vault_path, sample_passphrase) -> None:
        """An invalid token returns None."""
        km = KeyManager(tmp_vault_path)
        master_key = km.derive_master_key(sample_passphrase)
        sm = SessionManager(tmp_vault_path)
        sm.create_session(master_key)
        result = sm.validate_token("not-a-real-token")
        assert result is None

    def test_clear_session(self, tmp_vault_path, sample_passphrase) -> None:
        """Clearing a session invalidates the token."""
        km = KeyManager(tmp_vault_path)
        master_key = km.derive_master_key(sample_passphrase)
        sm = SessionManager(tmp_vault_path)
        token = sm.create_session(master_key)
        sm.clear_session()
        assert sm.validate_token(token) is None

    def test_is_active(self, tmp_vault_path, sample_passphrase) -> None:
        """is_active() is True after session creation."""
        km = KeyManager(tmp_vault_path)
        master_key = km.derive_master_key(sample_passphrase)
        sm = SessionManager(tmp_vault_path)
        sm.create_session(master_key)
        assert sm.is_active() is True
