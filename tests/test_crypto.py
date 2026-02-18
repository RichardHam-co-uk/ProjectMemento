"""
Unit tests for vault.security.crypto (KeyManager).
"""
import pytest
from pathlib import Path

from vault.security.crypto import KeyManager


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def key_manager(vault_root: Path) -> KeyManager:
    return KeyManager(vault_root)


class TestKeyDerivation:
    def test_derive_master_key_returns_32_bytes(self, key_manager):
        key = key_manager.derive_master_key("a-valid-passphrase-123")
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_same_passphrase_same_key(self, vault_root):
        km1 = KeyManager(vault_root)
        km2 = KeyManager(vault_root)
        key1 = km1.derive_master_key("same-passphrase-here!")
        key2 = km2.derive_master_key("same-passphrase-here!")
        assert key1 == key2

    def test_different_passphrase_different_key(self, vault_root):
        km = KeyManager(vault_root)
        key1 = km.derive_master_key("first-passphrase-abc!")
        key2 = km.derive_master_key("second-passphrase-xyz!")
        assert key1 != key2

    def test_salt_file_created(self, vault_root, key_manager):
        key_manager.derive_master_key("test-passphrase-12345")
        assert (vault_root / ".salt").exists()

    def test_salt_file_is_16_bytes(self, vault_root, key_manager):
        key_manager.derive_master_key("test-passphrase-12345")
        salt = (vault_root / ".salt").read_bytes()
        assert len(salt) == 16

    def test_passphrase_too_short_raises(self, key_manager):
        with pytest.raises(ValueError, match="12"):
            key_manager.derive_master_key("short")

    def test_derive_conversation_key_returns_fernet_key(self, key_manager):
        master = key_manager.derive_master_key("test-passphrase-12345")
        conv_key = key_manager.derive_conversation_key(master, "conv-abc123")
        assert isinstance(conv_key, bytes)
        # Fernet keys are 44 bytes (32 bytes base64url-encoded)
        assert len(conv_key) == 44

    def test_derive_conversation_key_is_deterministic(self, key_manager):
        master = key_manager.derive_master_key("test-passphrase-12345")
        key1 = key_manager.derive_conversation_key(master, "conv-abc")
        key2 = key_manager.derive_conversation_key(master, "conv-abc")
        assert key1 == key2

    def test_different_conversation_ids_give_different_keys(self, key_manager):
        master = key_manager.derive_master_key("test-passphrase-12345")
        key1 = key_manager.derive_conversation_key(master, "conv-1")
        key2 = key_manager.derive_conversation_key(master, "conv-2")
        assert key1 != key2

    def test_get_fernet_returns_fernet_instance(self, key_manager):
        from cryptography.fernet import Fernet
        master = key_manager.derive_master_key("test-passphrase-12345")
        fernet = key_manager.get_fernet(master, "conv-xyz")
        assert isinstance(fernet, Fernet)

    def test_cache_master_key(self, key_manager):
        master = key_manager.derive_master_key("test-passphrase-12345")
        key_manager.cache_master_key(master)
        assert key_manager._master_key == master

    def test_derive_conversation_key_wrong_key_length(self, key_manager):
        with pytest.raises(ValueError):
            key_manager.derive_conversation_key(b"tooshort", "conv-1")

    def test_derive_conversation_key_empty_id(self, key_manager):
        master = key_manager.derive_master_key("test-passphrase-12345")
        with pytest.raises(ValueError):
            key_manager.derive_conversation_key(master, "")
