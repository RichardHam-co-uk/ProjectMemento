# Task T-test-pipeline: Real Tests for ChatGPT Import Pipeline

**Target file:** `tests/test_pipeline.py` (replace placeholder)
**Recommended model:** GPT-4o-mini or Claude Haiku 4.5
**Effort:** Medium (~1.5 hours)
**Dependencies:** `vault/ingestion/chatgpt.py`, `vault/storage/db.py`

---

## Context

`tests/test_pipeline.py` currently has a single `test_placeholder`. Replace it
with a real test suite for the `run_import()` function in
`vault.ingestion.chatgpt`, which orchestrates the full import pipeline.

## Files to Read First

- `vault/ingestion/chatgpt.py` — full file, especially `run_import()`
- `vault/storage/db.py` — VaultDB
- `vault/storage/models.py` — Conversation, Message

## run_import() API

```python
from vault.ingestion.chatgpt import run_import
from vault.ingestion.base import ImportResult

result: ImportResult = run_import(file_path=Path(...), db=VaultDB(...))
# ImportResult fields: imported (int), skipped (int), failed (int), errors (list[str])
```

## Fixtures & Helpers (reuse from test_chatgpt_adapter.py pattern)

```python
import json, pytest
from pathlib import Path
from vault.storage.db import VaultDB
from vault.ingestion.chatgpt import run_import

def write_export(tmp_path, conversations):
    f = tmp_path / "conversations.json"
    f.write_text(json.dumps(conversations))
    return f

def make_conv(title="Test", msgs=None, conv_id="test-uuid-1234"):
    msgs = msgs or [("user", "Hello"), ("assistant", "Hi")]
    mapping = {"root": {"id": "root", "message": None, "parent": None,
                        "children": ["msg0"] if msgs else []}}
    for i, (role, content) in enumerate(msgs):
        nid = f"msg{i}"
        next_nid = f"msg{i+1}" if i + 1 < len(msgs) else None
        mapping[nid] = {
            "id": nid,
            "message": {
                "id": nid,
                "author": {"role": role},
                "content": {"content_type": "text", "parts": [content]},
                "create_time": 1700000000.0 + i,
                "metadata": {},
            },
            "parent": "root" if i == 0 else f"msg{i-1}",
            "children": [next_nid] if next_nid else [],
        }
    return {"title": title, "create_time": 1700000000.0,
            "update_time": 1700000100.0, "conversation_id": conv_id,
            "mapping": mapping}

@pytest.fixture
def db(tmp_path):
    vault_db = VaultDB(tmp_path / "vault.db")
    vault_db.init_schema()
    return vault_db
```

## Tests to Write

```python
class TestImportPipeline:

    def test_import_single_conversation(self, tmp_path, db):
        f = write_export(tmp_path, [make_conv("My Chat")])
        result = run_import(f, db)
        assert result.imported == 1
        assert result.failed == 0
        assert db.count_conversations() == 1

    def test_import_messages_persisted(self, tmp_path, db):
        f = write_export(tmp_path, [make_conv(msgs=[("user","Q"), ("assistant","A")])])
        run_import(f, db)
        assert db.count_messages() == 2

    def test_import_multiple_conversations(self, tmp_path, db):
        convs = [make_conv(f"Chat {i}", conv_id=f"uuid-{i}") for i in range(5)]
        f = write_export(tmp_path, convs)
        result = run_import(f, db)
        assert result.imported == 5
        assert db.count_conversations() == 5

    def test_deduplication_skips_duplicate(self, tmp_path, db):
        """Importing the same file twice should skip on the second run."""
        f = write_export(tmp_path, [make_conv("Same Chat")])
        result1 = run_import(f, db)
        result2 = run_import(f, db)
        assert result1.imported == 1
        assert result2.skipped == 1
        assert result2.imported == 0
        assert db.count_conversations() == 1

    def test_import_file_not_found(self, tmp_path, db):
        result = run_import(tmp_path / "ghost.json", db)
        assert result.failed == 1
        assert len(result.errors) == 1

    def test_import_invalid_json(self, tmp_path, db):
        f = tmp_path / "bad.json"
        f.write_text("not json {{")
        result = run_import(f, db)
        assert result.failed >= 1

    def test_import_result_fields(self, tmp_path, db):
        """ImportResult has int fields: imported, skipped, failed."""
        f = write_export(tmp_path, [make_conv()])
        result = run_import(f, db)
        assert isinstance(result.imported, int)
        assert isinstance(result.skipped, int)
        assert isinstance(result.failed, int)
        assert isinstance(result.errors, list)

    def test_import_empty_array(self, tmp_path, db):
        f = write_export(tmp_path, [])
        result = run_import(f, db)
        assert result.imported == 0
        assert result.failed == 0
```

## Conventions

- Use `pytest` and `tmp_path`.
- Define `write_export`, `make_conv`, and `db` fixture at module level.
- Remove `test_placeholder` entirely.
- Keep `TestImportPipeline` class name (change from `TestPipeline` if needed).

---

## Console Prompt

```
Read vault/ingestion/chatgpt.py (especially run_import), vault/storage/db.py,
and vault/storage/models.py in full.

Replace tests/test_pipeline.py with a real test suite for run_import().
Define write_export(), make_conv(), and a db fixture at module level.
Cover: import single conversation, messages persisted, import multiple
conversations, deduplication skips on second import, file not found returns
failed=1, invalid JSON returns failed>=1, result fields are correct types,
empty array imports 0 conversations.

Remove test_placeholder. Use TestImportPipeline as the class name.
```
