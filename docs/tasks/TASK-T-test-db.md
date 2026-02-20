# Task T-test-db: Real Tests for VaultDB

**Target file:** `tests/test_db.py` (replace placeholder)
**Recommended model:** GPT-4o-mini or Qwen2.5-Coder
**Effort:** Medium (~1.5 hours)
**Dependencies:** `vault/storage/db.py`, `vault/storage/models.py`

---

## Context

`tests/test_db.py` currently has a single `test_placeholder`. Replace it with
a real test suite for `vault.storage.db.VaultDB`.

## Files to Read First

- `vault/storage/db.py` — full file (VaultDB class)
- `vault/storage/models.py` — Conversation, Message ORM models

## VaultDB API

```python
class VaultDB:
    def __init__(self, db_path: Path, echo: bool = False) -> None
    def init_schema(self) -> None
    def get_session(self) -> ContextManager[Session]
    def get_conversation(self, conv_id: str) -> Conversation | None
    def list_conversations(self, limit=100, offset=0, source=None) -> list[Conversation]
    def count_conversations(self) -> int
    def count_messages(self) -> int
    def get_messages_for_conversation(self, conv_id: str) -> list[Message]
    def add_conversation(self, conversation: Conversation) -> None
    def get_date_range(self) -> tuple[datetime|None, datetime|None]
    def get_source_counts(self) -> dict[str, int]
```

## Fixture & Helper

```python
import pytest
from datetime import datetime, timezone
from pathlib import Path
from vault.storage.db import VaultDB
from vault.storage.models import Conversation, Message

def make_conversation(conv_id="conv-001", source="chatgpt", title="Test", n_messages=2):
    messages = [
        Message(
            id=f"{conv_id}-msg{i}",
            conversation_id=conv_id,
            actor="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            timestamp=datetime(2025, 1, i + 1, tzinfo=timezone.utc).replace(tzinfo=None),
            metadata={},
        )
        for i in range(n_messages)
    ]
    return Conversation(
        id=conv_id,
        title=title,
        source=source,
        external_id=None,
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
        message_count=n_messages,
        metadata={},
        messages=messages,
    )

@pytest.fixture
def db(tmp_path):
    vault_db = VaultDB(tmp_path / "vault.db")
    vault_db.init_schema()
    return vault_db
```

## Tests to Write

```python
class TestVaultDB:

    def test_init_schema_creates_db_file(self, tmp_path):
        db_path = tmp_path / "vault.db"
        db = VaultDB(db_path)
        db.init_schema()
        assert db_path.exists()

    def test_count_conversations_empty(self, db):
        assert db.count_conversations() == 0

    def test_count_messages_empty(self, db):
        assert db.count_messages() == 0

    def test_add_and_get_conversation(self, db):
        conv = make_conversation("c-001")
        db.add_conversation(conv)
        fetched = db.get_conversation("c-001")
        assert fetched is not None
        assert fetched.title == "Test"

    def test_get_conversation_not_found(self, db):
        assert db.get_conversation("nonexistent") is None

    def test_count_after_add(self, db):
        db.add_conversation(make_conversation("c-001"))
        db.add_conversation(make_conversation("c-002"))
        assert db.count_conversations() == 2

    def test_count_messages_after_add(self, db):
        db.add_conversation(make_conversation("c-001", n_messages=3))
        assert db.count_messages() == 3

    def test_list_conversations_returns_all(self, db):
        for i in range(5):
            db.add_conversation(make_conversation(f"c-{i:03d}"))
        results = db.list_conversations(limit=10)
        assert len(results) == 5

    def test_list_conversations_limit(self, db):
        for i in range(10):
            db.add_conversation(make_conversation(f"c-{i:03d}"))
        results = db.list_conversations(limit=3)
        assert len(results) == 3

    def test_list_conversations_offset(self, db):
        for i in range(5):
            db.add_conversation(make_conversation(f"c-{i:03d}"))
        all_convs = db.list_conversations(limit=100)
        paged = db.list_conversations(limit=100, offset=2)
        assert len(paged) == 3

    def test_list_conversations_source_filter(self, db):
        db.add_conversation(make_conversation("c-001", source="chatgpt"))
        db.add_conversation(make_conversation("c-002", source="claude"))
        results = db.list_conversations(source="claude")
        assert all(c.source == "claude" for c in results)
        assert len(results) == 1

    def test_get_messages_for_conversation(self, db):
        db.add_conversation(make_conversation("c-001", n_messages=4))
        messages = db.get_messages_for_conversation("c-001")
        assert len(messages) == 4

    def test_get_messages_empty_conversation(self, db):
        db.add_conversation(make_conversation("c-001", n_messages=0))
        assert db.get_messages_for_conversation("c-001") == []

    def test_get_date_range_empty(self, db):
        oldest, newest = db.get_date_range()
        assert oldest is None and newest is None

    def test_get_date_range_with_data(self, db):
        db.add_conversation(make_conversation("c-001"))
        oldest, newest = db.get_date_range()
        assert oldest is not None and newest is not None

    def test_get_source_counts(self, db):
        db.add_conversation(make_conversation("c-001", source="chatgpt"))
        db.add_conversation(make_conversation("c-002", source="chatgpt"))
        db.add_conversation(make_conversation("c-003", source="claude"))
        counts = db.get_source_counts()
        assert counts["chatgpt"] == 2
        assert counts["claude"] == 1
```

## Conventions

- Use `pytest` and `tmp_path`.
- Define `make_conversation` and `db` fixture at module level.
- Remove `test_placeholder` entirely.
- Keep `TestVaultDB` class name.

---

## Console Prompt

```
Read vault/storage/db.py and vault/storage/models.py in full.

Replace tests/test_db.py with a real test suite. Define a module-level
make_conversation(conv_id, source, title, n_messages) helper and a db
pytest fixture that creates VaultDB with a temp SQLite file and calls
init_schema(). Cover: db file created, count is 0 when empty, add and
get conversation, get returns None for unknown id, count after add,
message count after add, list returns all, list respects limit and offset,
list filters by source, get_messages_for_conversation, empty message list,
get_date_range empty/populated, get_source_counts groups correctly.

Remove test_placeholder. Keep TestVaultDB class name.
```
