"""Tests for vault.storage.blobs (BlobStore)."""
from vault.storage.blobs import BlobStore
from vault.security.crypto import KeyManager


class TestBlobStore:
    """Test suite for BlobStore."""

    def test_placeholder(self) -> None:
        """Placeholder test — replace with real tests."""
        assert True

    def test_store_and_retrieve(self, tmp_vault_path, sample_passphrase) -> None:
        """Stored content can be retrieved and decrypted."""
        km = KeyManager(tmp_vault_path)
        master_key = km.derive_master_key(sample_passphrase)
        bs = BlobStore(tmp_vault_path / "blobs", km)
        content = b"Hello, vault!"
        conv_id = "test-conv-abc123"
        blob_id = bs.store(content, master_key, conv_id)
        retrieved = bs.retrieve(blob_id, master_key, conv_id)
        assert retrieved == content

    def test_delete_blob(self, tmp_vault_path, sample_passphrase) -> None:
        """Deleting a blob removes it from storage."""
        km = KeyManager(tmp_vault_path)
        master_key = km.derive_master_key(sample_passphrase)
        bs = BlobStore(tmp_vault_path / "blobs", km)
        blob_id = bs.store(b"delete me", master_key, "conv-del")
        assert bs.exists(blob_id)
        bs.delete(blob_id)
        assert not bs.exists(blob_id)
