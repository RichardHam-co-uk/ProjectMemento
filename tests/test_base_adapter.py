"""Tests for vault.ingestion.base."""
from datetime import datetime, timezone
from vault.ingestion.base import (
    ParsedMessage,
    ParsedConversation,
    ImportResult,
    normalize_timestamp,
    generate_conversation_hash,
    deduplicate_messages,
)


class TestBaseAdapter:
    """Test suite for base adapter utilities."""

    def test_placeholder(self) -> None:
        """Placeholder test — replace with real tests."""
        assert True

    def test_normalize_timestamp_float(self) -> None:
        """Unix float timestamps are converted to UTC datetime."""
        ts = 1700000000.0
        dt = normalize_timestamp(ts)
        assert dt.tzinfo == timezone.utc
        assert dt.timestamp() == ts

    def test_normalize_timestamp_none(self) -> None:
        """None returns datetime.now(UTC)."""
        dt = normalize_timestamp(None)
        assert dt.tzinfo == timezone.utc

    def test_normalize_timestamp_iso_string(self) -> None:
        """ISO strings are parsed correctly."""
        dt = normalize_timestamp("2024-01-15T10:30:00+00:00")
        assert dt.tzinfo is not None
        assert dt.year == 2024

    def test_normalize_timestamp_integer(self) -> None:
        """Integer timestamps are converted correctly."""
        ts = 1700000000
        dt = normalize_timestamp(ts)
        assert dt.timestamp() == float(ts)

    def test_generate_conversation_hash_consistent(self) -> None:
        """Same inputs always produce the same 64-char hash."""
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        h1 = generate_conversation_hash("chatgpt", "My Chat", ts)
        h2 = generate_conversation_hash("chatgpt", "My Chat", ts)
        assert h1 == h2
        assert len(h1) == 64

    def test_generate_conversation_hash_differs_by_source(self) -> None:
        """Different sources produce different hashes."""
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        h1 = generate_conversation_hash("chatgpt", "Title", ts)
        h2 = generate_conversation_hash("claude", "Title", ts)
        assert h1 != h2

    def test_deduplicate_messages_removes_duplicates(self) -> None:
        """Exact duplicate messages are removed."""
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        msg = ParsedMessage(id="1", actor="user", content="Hello", timestamp=ts)
        dup = ParsedMessage(id="2", actor="user", content="Hello", timestamp=ts)
        result = deduplicate_messages([msg, dup])
        assert len(result) == 1
        assert result[0].id == "1"

    def test_deduplicate_messages_preserves_order(self) -> None:
        """Deduplication preserves insertion order."""
        ts1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        ts2 = datetime(2024, 1, 2, tzinfo=timezone.utc)
        m1 = ParsedMessage(id="1", actor="user", content="First", timestamp=ts1)
        m2 = ParsedMessage(id="2", actor="assistant", content="Second", timestamp=ts2)
        result = deduplicate_messages([m1, m2])
        assert [m.id for m in result] == ["1", "2"]

    def test_import_result_defaults(self) -> None:
        """ImportResult starts with all zeros and empty errors."""
        r = ImportResult()
        assert r.imported == 0
        assert r.skipped == 0
        assert r.failed == 0
        assert r.errors == []
