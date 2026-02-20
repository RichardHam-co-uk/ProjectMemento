# Task T-test-session: Real Tests for SessionManager

**Target file:** `tests/test_session.py` (replace placeholder)
**Recommended model:** GPT-4o-mini or Claude Haiku 4.5
**Effort:** Medium (~1 hour)
**Dependencies:** `vault/security/session.py`

---

## Context

`tests/test_session.py` currently has a single `test_placeholder`. Replace it
with a real test suite for `vault.security.session.SessionManager`.

## Files to Read First

- `vault/security/session.py` — full file

## SessionManager API

```python
class SessionManager:
    def __init__(self, vault_root: Path, timeout_minutes: int = 30) -> None
    def create_session(self, master_key: bytes) -> str   # returns token (hex str)
    def validate_token(self, token: str) -> bytes | None # returns master_key or None
    def clear_session(self) -> None
    def is_active(self) -> bool
```

## Tests to Write

```python
import pytest
from pathlib import Path
from vault.security.session import SessionManager

MASTER_KEY = b"\xab" * 32   # 32 bytes of dummy key

class TestSessionManager:

    def test_create_session_returns_token(self, tmp_path):
        sm = SessionManager(tmp_path)
        token = sm.create_session(MASTER_KEY)
        assert isinstance(token, str) and len(token) == 64  # 32 bytes hex

    def test_session_file_created(self, tmp_path):
        sm = SessionManager(tmp_path)
        sm.create_session(MASTER_KEY)
        assert (tmp_path / ".session").exists()

    def test_validate_token_returns_master_key(self, tmp_path):
        sm = SessionManager(tmp_path)
        token = sm.create_session(MASTER_KEY)
        recovered = sm.validate_token(token)
        assert recovered == MASTER_KEY

    def test_validate_wrong_token_returns_none(self, tmp_path):
        sm = SessionManager(tmp_path)
        sm.create_session(MASTER_KEY)
        assert sm.validate_token("a" * 64) is None

    def test_validate_no_session_returns_none(self, tmp_path):
        sm = SessionManager(tmp_path)
        assert sm.validate_token("a" * 64) is None

    def test_is_active_true_after_create(self, tmp_path):
        sm = SessionManager(tmp_path)
        sm.create_session(MASTER_KEY)
        assert sm.is_active() is True

    def test_is_active_false_before_create(self, tmp_path):
        sm = SessionManager(tmp_path)
        assert sm.is_active() is False

    def test_clear_session_destroys_file(self, tmp_path):
        sm = SessionManager(tmp_path)
        sm.create_session(MASTER_KEY)
        sm.clear_session()
        assert not (tmp_path / ".session").exists()

    def test_clear_session_invalidates_token(self, tmp_path):
        sm = SessionManager(tmp_path)
        token = sm.create_session(MASTER_KEY)
        sm.clear_session()
        assert sm.validate_token(token) is None

    def test_is_active_false_after_clear(self, tmp_path):
        sm = SessionManager(tmp_path)
        sm.create_session(MASTER_KEY)
        sm.clear_session()
        assert sm.is_active() is False

    def test_clear_session_noop_when_no_session(self, tmp_path):
        """clear_session() should not raise when no session exists."""
        sm = SessionManager(tmp_path)
        sm.clear_session()   # should not raise

    def test_create_requires_32_byte_key(self, tmp_path):
        sm = SessionManager(tmp_path)
        with pytest.raises(ValueError):
            sm.create_session(b"tooshort")

    def test_expired_session_returns_none(self, tmp_path):
        """A session with timeout=0 should be immediately expired."""
        import time
        sm = SessionManager(tmp_path, timeout_minutes=0)
        token = sm.create_session(MASTER_KEY)
        time.sleep(0.1)
        assert sm.validate_token(token) is None

    def test_session_file_not_readable_as_plaintext_key(self, tmp_path):
        """The master key must not appear verbatim in the session file."""
        sm = SessionManager(tmp_path)
        sm.create_session(MASTER_KEY)
        raw = (tmp_path / ".session").read_bytes()
        assert MASTER_KEY not in raw
```

## Conventions

- Use `pytest` and `tmp_path`.
- Remove `test_placeholder` entirely.
- Keep `TestSessionManager` class name.
- `MASTER_KEY = b"\\xab" * 32` as module-level constant.

---

## Console Prompt

```
Read vault/security/session.py in full.

Replace tests/test_session.py with a real test suite. Use pytest and
tmp_path. MASTER_KEY = b"\xab" * 32 as a module-level constant. Cover:
create_session returns 64-char hex token, .session file is created,
validate_token returns master key, wrong token returns None, no session
returns None, is_active true after create, is_active false before create,
clear_session removes the file, clear_session invalidates the token,
is_active false after clear, clear is noop when no session, create raises
ValueError for non-32-byte key, expired session (timeout=0) returns None,
master key not stored verbatim on disk.

Remove test_placeholder. Keep TestSessionManager class name.
```
