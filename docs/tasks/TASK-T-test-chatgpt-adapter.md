# Task T-test-chatgpt-adapter: Real Tests for ChatGPTAdapter

**Target file:** `tests/test_chatgpt_adapter.py` (replace placeholder)
**Recommended model:** GPT-4o-mini or Qwen2.5-Coder
**Effort:** Medium (~1.5 hours)
**Dependencies:** `vault/ingestion/chatgpt.py`, `vault/ingestion/base.py`

---

## Context

`tests/test_chatgpt_adapter.py` currently has a single `test_placeholder`.
Replace it with a real test suite for `vault.ingestion.chatgpt.ChatGPTAdapter`.

## Files to Read First

- `vault/ingestion/chatgpt.py` — full file
- `vault/ingestion/base.py` — `ParsedConversation`, `ParsedMessage`

## ChatGPTAdapter API

```python
class ChatGPTAdapter:
    @property
    def provider_name(self) -> str          # returns "chatgpt"
    def parse(self, file_path: Path) -> list[ParsedConversation]
    def validate_format(self, file_path: Path) -> bool
```

## Sample Data Helper

Use this helper to write valid ChatGPT-format JSON to a temp file:

```python
import json
from pathlib import Path

def write_export(tmp_path: Path, conversations: list) -> Path:
    f = tmp_path / "conversations.json"
    f.write_text(json.dumps(conversations))
    return f

def make_conv(title="Test", msgs=None):
    """Build a minimal valid ChatGPT conversation object."""
    msgs = msgs or [("user", "Hello"), ("assistant", "Hi!")]
    mapping = {}
    node_ids = ["root"] + [f"msg{i}" for i in range(len(msgs))]

    mapping["root"] = {
        "id": "root",
        "message": None,
        "parent": None,
        "children": [node_ids[1]] if len(node_ids) > 1 else [],
    }
    for i, (role, content) in enumerate(msgs):
        nid = node_ids[i + 1]
        next_nid = node_ids[i + 2] if i + 2 < len(node_ids) else None
        mapping[nid] = {
            "id": nid,
            "message": {
                "id": nid,
                "author": {"role": role},
                "content": {"content_type": "text", "parts": [content]},
                "create_time": 1700000000.0 + i,
                "metadata": {},
            },
            "parent": node_ids[i],
            "children": [next_nid] if next_nid else [],
        }
    return {
        "title": title,
        "create_time": 1700000000.0,
        "update_time": 1700000100.0,
        "conversation_id": "test-uuid-1234",
        "mapping": mapping,
    }
```

## Tests to Write

```python
class TestChatGPTAdapter:

    def test_provider_name(self):
        assert ChatGPTAdapter().provider_name == "chatgpt"

    def test_parse_single_conversation(self, tmp_path):
        f = write_export(tmp_path, [make_conv("My Chat")])
        convs = ChatGPTAdapter().parse(f)
        assert len(convs) == 1
        assert convs[0].title == "My Chat"
        assert convs[0].source == "chatgpt"

    def test_parse_two_messages(self, tmp_path):
        f = write_export(tmp_path, [make_conv(msgs=[("user", "Q"), ("assistant", "A")])])
        convs = ChatGPTAdapter().parse(f)
        msgs = convs[0].messages
        assert len(msgs) == 2
        assert msgs[0].actor == "user"
        assert msgs[0].content == "Q"
        assert msgs[1].actor == "assistant"
        assert msgs[1].content == "A"

    def test_parse_multiple_conversations(self, tmp_path):
        f = write_export(tmp_path, [make_conv("Chat A"), make_conv("Chat B")])
        convs = ChatGPTAdapter().parse(f)
        assert len(convs) == 2

    def test_system_messages_filtered(self, tmp_path):
        """System-role messages should not appear in parsed output."""
        f = write_export(tmp_path, [make_conv(msgs=[
            ("system", "You are a helpful assistant."),
            ("user", "Hello"),
            ("assistant", "Hi"),
        ])])
        convs = ChatGPTAdapter().parse(f)
        actors = [m.actor for m in convs[0].messages]
        assert "system" not in actors
        assert len(actors) == 2

    def test_empty_content_parts_filtered(self, tmp_path):
        """Messages with blank content should be dropped."""
        conv = make_conv(msgs=[("user", ""), ("assistant", "Hi")])
        f = write_export(tmp_path, [conv])
        convs = ChatGPTAdapter().parse(f)
        assert all(m.content.strip() for m in convs[0].messages)

    def test_parse_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ChatGPTAdapter().parse(tmp_path / "nonexistent.json")

    def test_parse_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not json at all {{{{")
        with pytest.raises(ValueError):
            ChatGPTAdapter().parse(f)

    def test_parse_json_object_not_array(self, tmp_path):
        f = tmp_path / "obj.json"
        f.write_text('{"title": "foo"}')
        with pytest.raises(ValueError):
            ChatGPTAdapter().parse(f)

    def test_validate_format_valid(self, tmp_path):
        f = write_export(tmp_path, [make_conv()])
        assert ChatGPTAdapter().validate_format(f) is True

    def test_validate_format_invalid(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text('[{"no_mapping": true}]')
        assert ChatGPTAdapter().validate_format(f) is False

    def test_validate_format_missing_file(self, tmp_path):
        assert ChatGPTAdapter().validate_format(tmp_path / "ghost.json") is False

    def test_external_id_captured(self, tmp_path):
        f = write_export(tmp_path, [make_conv()])
        convs = ChatGPTAdapter().parse(f)
        assert convs[0].external_id == "test-uuid-1234"

    def test_timestamps_are_utc_aware(self, tmp_path):
        from datetime import timezone
        f = write_export(tmp_path, [make_conv()])
        convs = ChatGPTAdapter().parse(f)
        assert convs[0].created_at.tzinfo is not None
```

## Conventions

- Use `pytest` and `tmp_path`.
- Put `write_export` and `make_conv` as module-level helpers (not inside
  the test class).
- Remove `test_placeholder` entirely.
- Keep `TestChatGPTAdapter` class name.

---

## Console Prompt

```
Read vault/ingestion/chatgpt.py and vault/ingestion/base.py in full.

Replace tests/test_chatgpt_adapter.py with real tests. Define two
module-level helpers: write_export(tmp_path, convs) and make_conv(title,
msgs) to produce ChatGPT-format JSON fixtures. Cover: provider_name,
single/multi conversation parse, user+assistant message order, system
messages filtered out, blank content filtered, FileNotFoundError, invalid
JSON ValueError, non-array JSON ValueError, validate_format true/false/
missing, external_id captured, timestamps timezone-aware.

Remove test_placeholder. Keep TestChatGPTAdapter class name.
```
