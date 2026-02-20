# Task T-test-blobs: Real Tests for BlobStore

**Target file:** `tests/test_blobs.py` (replace placeholder)
**Recommended model:** GPT-4o-mini or Claude Haiku 4.5
**Effort:** Medium (~1.5 hours)
**Dependencies:** `vault/storage/blobs.py`, `vault/security/crypto.py`

---

## Context

`tests/test_blobs.py` currently has a single `test_placeholder`. Replace it
with a real test suite for `vault.storage.blobs.BlobStore`.

## Files to Read First

- `vault/storage/blobs.py` — full file
- `vault/security/crypto.py` — KeyManager (needed to create BlobStore)

## BlobStore API

```python
class BlobStore:
    def __init__(self, root_path: Path, key_manager: KeyManager) -> None
    def store(self, content: bytes, conversation_id: str, blob_id: str | None = None) -> str
    def retrieve(self, blob_id: str, conversation_id: str) -> bytes
    def delete(self, blob_id: str) -> bool
    def exists(self, blob_id: str) -> bool
    def get_total_size(self) -> int
```

## Fixture Pattern

```python
import pytest
from pathlib import Path
from vault.storage.blobs import BlobStore
from vault.security.crypto import KeyManager

PASSPHRASE = "test-passphrase-long-enough-123"

@pytest.fixture
def vault_root(tmp_path):
    (tmp_path / "blobs").mkdir()
    return tmp_path

@pytest.fixture
def key_manager(vault_root):
    km = KeyManager(vault_root)
    master = km.derive_master_key(PASSPHRASE)
    km.cache_master_key(master)
    return km

@pytest.fixture
def blob_store(vault_root, key_manager):
    return BlobStore(vault_root / "blobs", key_manager)
```

## Tests to Write

```python
class TestBlobStore:

    def test_store_returns_blob_id(self, blob_store):
        blob_id = blob_store.store(b"hello world", "conv-001")
        assert isinstance(blob_id, str) and len(blob_id) > 0

    def test_store_and_retrieve_roundtrip(self, blob_store):
        content = b"Secret content for testing"
        blob_id = blob_store.store(content, "conv-001")
        retrieved = blob_store.retrieve(blob_id, "conv-001")
        assert retrieved == content

    def test_retrieve_wrong_conversation_id_fails(self, blob_store):
        """Decryption should fail with the wrong conversation key."""
        blob_id = blob_store.store(b"secret", "conv-aaa")
        with pytest.raises(Exception):
            blob_store.retrieve(blob_id, "conv-bbb")

    def test_blob_file_exists_on_disk(self, blob_store, vault_root):
        blob_id = blob_store.store(b"data", "conv-001")
        assert blob_store.exists(blob_id)

    def test_delete_removes_blob(self, blob_store):
        blob_id = blob_store.store(b"to be deleted", "conv-001")
        assert blob_store.exists(blob_id)
        result = blob_store.delete(blob_id)
        assert result is True
        assert not blob_store.exists(blob_id)

    def test_delete_nonexistent_blob_returns_false(self, blob_store):
        result = blob_store.delete("00000000-0000-0000-0000-000000000000")
        assert result is False

    def test_retrieve_after_delete_raises(self, blob_store):
        blob_id = blob_store.store(b"data", "conv-001")
        blob_store.delete(blob_id)
        with pytest.raises(Exception):
            blob_store.retrieve(blob_id, "conv-001")

    def test_stored_file_is_not_plaintext(self, blob_store, vault_root):
        """The .enc file on disk must not contain the plaintext."""
        content = b"very secret text that must not appear on disk"
        blob_id = blob_store.store(content, "conv-001")
        # Find the .enc file and check its raw bytes
        enc_files = list(vault_root.rglob("*.enc"))
        assert len(enc_files) >= 1
        raw = enc_files[0].read_bytes()
        assert content not in raw

    def test_store_custom_blob_id(self, blob_store):
        import uuid
        custom_id = str(uuid.uuid4())
        returned_id = blob_store.store(b"data", "conv-001", blob_id=custom_id)
        assert returned_id == custom_id
        assert blob_store.exists(custom_id)

    def test_large_content_roundtrip(self, blob_store):
        content = b"x" * 1_000_000  # 1 MB
        blob_id = blob_store.store(content, "conv-big")
        assert blob_store.retrieve(blob_id, "conv-big") == content

    def test_get_total_size_increases_after_store(self, blob_store):
        size_before = blob_store.get_total_size()
        blob_store.store(b"some data to add", "conv-001")
        size_after = blob_store.get_total_size()
        assert size_after > size_before
```

## Conventions

- Use `pytest` fixtures (`tmp_path`, custom fixtures above).
- Remove `test_placeholder` entirely.
- Keep the `TestBlobStore` class name.
- Do not mock the crypto layer — use real key derivation.

---

## Console Prompt

```
Read vault/storage/blobs.py and vault/security/crypto.py in full.

Replace tests/test_blobs.py with a real test suite. Use pytest fixtures
(tmp_path). Cover: store returns a blob_id, store+retrieve roundtrip,
wrong conversation_id fails decryption, blob file exists on disk after
store, delete removes the blob, delete returns False for nonexistent blob,
retrieve after delete raises, stored file is not plaintext, custom blob_id
is honoured, large content roundtrip, get_total_size increases after store.

Remove test_placeholder. Keep TestBlobStore class name.
```
