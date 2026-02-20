# Task T-test-crypto: Real Tests for KeyManager

**Target file:** `tests/test_crypto.py` (replace placeholder)
**Recommended model:** GPT-4o-mini or Claude Haiku 4.5
**Effort:** Medium (~1.5 hours)
**Dependencies:** `vault/security/crypto.py` must exist

---

## Context

`tests/test_crypto.py` currently has a single `test_placeholder` that always
passes. Replace it with a real test suite for `vault.security.crypto.KeyManager`.

## Files to Read First

- `vault/security/crypto.py` — full file (understand KeyManager methods and args)
- `tests/conftest.py` — shared fixtures

## KeyManager API (from crypto.py)

```python
class KeyManager:
    def __init__(self, vault_root: Path) -> None
    def derive_master_key(self, passphrase: str) -> bytes          # 32 bytes
    def derive_conversation_key(self, master_key: bytes, conversation_id: str) -> bytes
    def get_fernet(self, master_key: bytes, conversation_id: str) -> Fernet
    def cache_master_key(self, key: bytes) -> None
    def get_cached_key(self) -> bytes | None
    def clear_cached_key(self) -> None
    def validate_passphrase(self, passphrase: str) -> tuple[bool, str]
    def verify_passphrase(self, passphrase: str) -> bool
    def get_master_key_hash(self, master_key: bytes) -> str
```

## Tests to Write

Use `pytest` and `tmp_path` fixture for temporary directories.

```python
import pytest
from pathlib import Path
from vault.security.crypto import KeyManager

class TestKeyManager:

    def test_derive_master_key_returns_32_bytes(self, tmp_path):
        km = KeyManager(tmp_path)
        key = km.derive_master_key("correct-horse-battery-staple-123")
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_same_passphrase_same_key(self, tmp_path):
        """Same passphrase on same vault produces same key (deterministic)."""
        km = KeyManager(tmp_path)
        key1 = km.derive_master_key("my-long-passphrase-here")
        key2 = km.derive_master_key("my-long-passphrase-here")
        assert key1 == key2

    def test_different_passphrase_different_key(self, tmp_path):
        km = KeyManager(tmp_path)
        key1 = km.derive_master_key("correct-horse-battery-staple-123")
        key2 = km.derive_master_key("wrong-horse-battery-staple-999")
        assert key1 != key2

    def test_salt_file_created(self, tmp_path):
        km = KeyManager(tmp_path)
        km.derive_master_key("passphrase-long-enough")
        assert (tmp_path / ".salt").exists()

    def test_salt_reused_across_instances(self, tmp_path):
        """A new KeyManager instance for the same vault reads the existing salt."""
        km1 = KeyManager(tmp_path)
        key1 = km1.derive_master_key("shared-passphrase-12345")
        km2 = KeyManager(tmp_path)
        key2 = km2.derive_master_key("shared-passphrase-12345")
        assert key1 == key2

    def test_derive_master_key_short_passphrase_raises(self, tmp_path):
        km = KeyManager(tmp_path)
        with pytest.raises((ValueError, Exception)):
            km.derive_master_key("short")

    def test_derive_conversation_key_deterministic(self, tmp_path):
        km = KeyManager(tmp_path)
        master = km.derive_master_key("passphrase-long-enough-12")
        k1 = km.derive_conversation_key(master, "conv-abc")
        k2 = km.derive_conversation_key(master, "conv-abc")
        assert k1 == k2

    def test_derive_conversation_key_unique_per_conversation(self, tmp_path):
        km = KeyManager(tmp_path)
        master = km.derive_master_key("passphrase-long-enough-12")
        k1 = km.derive_conversation_key(master, "conv-aaa")
        k2 = km.derive_conversation_key(master, "conv-bbb")
        assert k1 != k2

    def test_get_fernet_encrypt_decrypt_roundtrip(self, tmp_path):
        km = KeyManager(tmp_path)
        master = km.derive_master_key("passphrase-long-enough-12")
        fernet = km.get_fernet(master, "conv-xyz")
        plaintext = b"Hello, secret world!"
        ciphertext = fernet.encrypt(plaintext)
        assert fernet.decrypt(ciphertext) == plaintext

    def test_cache_and_retrieve_master_key(self, tmp_path):
        km = KeyManager(tmp_path)
        master = km.derive_master_key("passphrase-long-enough-12")
        km.cache_master_key(master)
        assert km.get_cached_key() == master

    def test_clear_cached_key(self, tmp_path):
        km = KeyManager(tmp_path)
        master = km.derive_master_key("passphrase-long-enough-12")
        km.cache_master_key(master)
        km.clear_cached_key()
        assert km.get_cached_key() is None

    def test_validate_passphrase_short(self, tmp_path):
        km = KeyManager(tmp_path)
        valid, msg = km.validate_passphrase("short")
        assert valid is False
        assert isinstance(msg, str) and len(msg) > 0

    def test_validate_passphrase_long_enough(self, tmp_path):
        km = KeyManager(tmp_path)
        valid, msg = km.validate_passphrase("correct-horse-battery-staple")
        assert valid is True
```

## Conventions

- Use `pytest` with `tmp_path` fixture (built-in — no extra imports needed).
- No mocking — use real Argon2 derivation (it's fast enough for tests).
- Remove the `test_placeholder` method entirely.
- Keep the `TestKeyManager` class name.
- Google-style docstrings on each test.

---

## Console Prompt

```
Read vault/security/crypto.py in full to understand the KeyManager class
and all its methods. Read tests/conftest.py for any shared fixtures.

Replace tests/test_crypto.py with a real test suite. Use pytest and the
tmp_path fixture. Cover: key derivation returns 32 bytes, same passphrase
produces same key, different passphrases produce different keys, salt file
is created and reused, short passphrase raises, per-conversation key is
deterministic and unique, Fernet encrypt/decrypt roundtrip works, key
caching and clearing works, passphrase validation returns (bool, str).

Remove the test_placeholder method. Keep the TestKeyManager class name.
```
