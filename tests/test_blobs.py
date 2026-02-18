"""
Unit tests for vault.storage.blobs (BlobStore).
"""
import pytest
from pathlib import Path

from vault.security.crypto import KeyManager
from vault.storage.blobs import BlobStore


PASSPHRASE = "test-passphrase-blobs-123!"
CONV_ID = "test-conversation-abc"


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def key_manager(vault_root: Path) -> KeyManager:
    return KeyManager(vault_root)


@pytest.fixture
def master_key(key_manager: KeyManager) -> bytes:
    return key_manager.derive_master_key(PASSPHRASE)


@pytest.fixture
def blob_store(vault_root: Path, key_manager: KeyManager) -> BlobStore:
    return BlobStore(vault_root / "blobs", key_manager)


class TestBlobStore:
    def test_store_returns_uuid_string(self, blob_store, master_key):
        blob_id = blob_store.store(b"hello world", master_key, CONV_ID)
        assert isinstance(blob_id, str)
        assert len(blob_id) == 36  # UUID format

    def test_retrieve_returns_original_content(self, blob_store, master_key):
        content = b"Secret message content here"
        blob_id = blob_store.store(content, master_key, CONV_ID)
        retrieved = blob_store.retrieve(blob_id, master_key, CONV_ID)
        assert retrieved == content

    def test_roundtrip_unicode_content(self, blob_store, master_key):
        content = "Hello, 世界! Привет мир! 🌍".encode("utf-8")
        blob_id = blob_store.store(content, master_key, CONV_ID)
        retrieved = blob_store.retrieve(blob_id, master_key, CONV_ID)
        assert retrieved == content

    def test_roundtrip_large_content(self, blob_store, master_key):
        content = b"X" * 100_000
        blob_id = blob_store.store(content, master_key, CONV_ID)
        retrieved = blob_store.retrieve(blob_id, master_key, CONV_ID)
        assert retrieved == content

    def test_file_exists_in_sharded_dir(self, blob_store, master_key, vault_root):
        blob_id = blob_store.store(b"test", master_key, CONV_ID)
        prefix = blob_id[:2]
        expected_path = vault_root / "blobs" / prefix / f"{blob_id}.enc"
        assert expected_path.exists()

    def test_wrong_conversation_id_fails_decryption(self, blob_store, master_key):
        blob_id = blob_store.store(b"secret", master_key, CONV_ID)
        with pytest.raises((ValueError, Exception)):
            blob_store.retrieve(blob_id, master_key, "different-conversation")

    def test_missing_blob_raises_file_not_found(self, blob_store, master_key):
        fake_id = "00000000-0000-0000-0000-000000000000"
        with pytest.raises(FileNotFoundError):
            blob_store.retrieve(fake_id, master_key, CONV_ID)

    def test_empty_content_raises(self, blob_store, master_key):
        with pytest.raises(ValueError):
            blob_store.store(b"", master_key, CONV_ID)

    def test_delete_removes_file(self, blob_store, master_key, vault_root):
        blob_id = blob_store.store(b"to be deleted", master_key, CONV_ID)
        prefix = blob_id[:2]
        path = vault_root / "blobs" / prefix / f"{blob_id}.enc"
        assert path.exists()
        blob_store.delete(blob_id)
        assert not path.exists()

    def test_delete_nonexistent_blob_returns_false(self, blob_store):
        fake_id = "00000000-0000-0000-0000-000000000001"
        result = blob_store.delete(fake_id)
        assert result is False

    def test_multiple_blobs_same_conversation(self, blob_store, master_key):
        ids = []
        for i in range(10):
            content = f"Message {i}".encode()
            blob_id = blob_store.store(content, master_key, CONV_ID)
            ids.append((blob_id, content))

        for blob_id, original in ids:
            retrieved = blob_store.retrieve(blob_id, master_key, CONV_ID)
            assert retrieved == original
