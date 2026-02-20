# Task T-test-base-adapter: Real Tests for Base Adapter Utilities

**Target file:** `tests/test_base_adapter.py` (replace placeholder)
**Recommended model:** Qwen2.5-Coder or Llama3 (Tier 1 suitable)
**Effort:** Small (~45 min)
**Dependencies:** `vault/ingestion/base.py`

---

## Context

`tests/test_base_adapter.py` currently has a single `test_placeholder`. Replace
it with a real test suite for the three utility functions in
`vault.ingestion.base`.

## Files to Read First

- `vault/ingestion/base.py` — full file (focus on the three utility functions)

## Functions to Test

```python
from vault.ingestion.base import (
    normalize_timestamp,
    generate_conversation_hash,
    deduplicate_messages,
    ParsedMessage,
)

normalize_timestamp(raw: float | str | int | None) -> datetime
    # float/int  → fromtimestamp(tz=UTC)
    # str        → fromisoformat (UTC assumed if no tzinfo)
    # None       → datetime.now(UTC)

generate_conversation_hash(source: str, title: str, created_at: datetime) -> str
    # Returns 64-char hex SHA-256

deduplicate_messages(messages: list[ParsedMessage]) -> list[ParsedMessage]
    # Removes exact duplicates (same actor, timestamp, content[:100])
    # Preserves order of first occurrence
```

## Tests to Write

```python
import pytest
from datetime import datetime, timezone
from vault.ingestion.base import (
    normalize_timestamp,
    generate_conversation_hash,
    deduplicate_messages,
    ParsedMessage,
)

DT = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

class TestNormalizeTimestamp:

    def test_float_to_utc_datetime(self):
        result = normalize_timestamp(1700000000.0)
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_int_to_utc_datetime(self):
        result = normalize_timestamp(1700000000)
        assert isinstance(result, datetime)

    def test_iso_string_with_tz(self):
        result = normalize_timestamp("2025-01-15T12:00:00+00:00")
        assert result.tzinfo is not None
        assert result.year == 2025

    def test_iso_string_without_tz_assumes_utc(self):
        result = normalize_timestamp("2025-01-15T12:00:00")
        assert result.tzinfo == timezone.utc

    def test_none_returns_now(self):
        before = datetime.now(timezone.utc)
        result = normalize_timestamp(None)
        after = datetime.now(timezone.utc)
        assert before <= result <= after

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError):
            normalize_timestamp("not-a-date")


class TestGenerateConversationHash:

    def test_returns_64_char_hex(self):
        h = generate_conversation_hash("chatgpt", "My Chat", DT)
        assert isinstance(h, str)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_deterministic(self):
        h1 = generate_conversation_hash("chatgpt", "My Chat", DT)
        h2 = generate_conversation_hash("chatgpt", "My Chat", DT)
        assert h1 == h2

    def test_different_source_different_hash(self):
        h1 = generate_conversation_hash("chatgpt", "My Chat", DT)
        h2 = generate_conversation_hash("claude", "My Chat", DT)
        assert h1 != h2

    def test_different_title_different_hash(self):
        h1 = generate_conversation_hash("chatgpt", "Title A", DT)
        h2 = generate_conversation_hash("chatgpt", "Title B", DT)
        assert h1 != h2

    def test_different_time_different_hash(self):
        dt2 = datetime(2025, 2, 1, tzinfo=timezone.utc)
        h1 = generate_conversation_hash("chatgpt", "My Chat", DT)
        h2 = generate_conversation_hash("chatgpt", "My Chat", dt2)
        assert h1 != h2


class TestDeduplicateMessages:

    def _msg(self, actor="user", content="Hello", ts=DT):
        return ParsedMessage(id="x", actor=actor, content=content, timestamp=ts)

    def test_no_duplicates_unchanged(self):
        msgs = [self._msg("user", "A"), self._msg("assistant", "B")]
        result = deduplicate_messages(msgs)
        assert len(result) == 2

    def test_exact_duplicate_removed(self):
        m = self._msg("user", "Hello")
        result = deduplicate_messages([m, m])
        assert len(result) == 1

    def test_different_actor_not_duplicate(self):
        msgs = [self._msg("user", "Hi"), self._msg("assistant", "Hi")]
        result = deduplicate_messages(msgs)
        assert len(result) == 2

    def test_preserves_order(self):
        msgs = [
            self._msg("user", "First"),
            self._msg("assistant", "Second"),
            self._msg("user", "First"),  # duplicate of first
        ]
        result = deduplicate_messages(msgs)
        assert len(result) == 2
        assert result[0].content == "First"
        assert result[1].content == "Second"

    def test_empty_list(self):
        assert deduplicate_messages([]) == []
```

## Conventions

- No fixtures required — use `DT` as a module-level datetime constant.
- Remove `test_placeholder` entirely.
- Keep class names `TestNormalizeTimestamp`, `TestGenerateConversationHash`,
  `TestDeduplicateMessages` (split from `TestBaseAdapter` if desired, or keep
  as one class — model's choice).

---

## Console Prompt

```
Read vault/ingestion/base.py in full (focus on normalize_timestamp,
generate_conversation_hash, deduplicate_messages, and ParsedMessage).

Replace tests/test_base_adapter.py with a real test suite. Define
DT = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc) at module level.

For normalize_timestamp: test float, int, ISO string with tz, ISO string
without tz (assumes UTC), None returns datetime.now, invalid string raises.
For generate_conversation_hash: returns 64-char hex, deterministic, changes
with different source/title/time.
For deduplicate_messages: no duplicates unchanged, exact duplicate removed,
different actor not duplicate, order preserved, empty list.

Remove test_placeholder.
```
