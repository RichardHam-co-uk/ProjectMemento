"""
Unit tests for vault.storage.models (ORM models) and vault.storage.database (VaultDB).
"""
import pytest
from datetime import datetime, timezone
from pathlib import Path

from vault.storage.database import VaultDB
from vault.storage.models import (
    ActorType,
    ArtifactType,
    Conversation,
    Message,
    PIIFinding,
    PIIType,
    SensitivityLevel,
)


@pytest.fixture
def db(tmp_path: Path) -> VaultDB:
    vault_db = VaultDB(tmp_path / "test.db")
    vault_db.create_schema()
    return vault_db


def _make_conversation(idx: int = 1, source: str = "chatgpt") -> Conversation:
    return Conversation(
        id=f"conv-id-{idx:04d}" + "0" * 56,  # pad to 64 chars
        source=source,
        external_id=f"ext-{idx}",
        title=f"Test Conversation {idx}",
        created_at=datetime(2025, 1, idx, 10, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, idx, 10, 0, tzinfo=timezone.utc),
        sensitivity=SensitivityLevel.INTERNAL,
        message_count=2,
        hash=f"hash{idx:060d}",
    )


def _make_message(conv_id: str, idx: int = 1) -> Message:
    # Pad idx to create a unique, valid 36-char UUID-like string
    padded = f"{idx:032d}"
    msg_id = f"{padded[:8]}-{padded[8:12]}-{padded[12:16]}-{padded[16:20]}-{padded[20:32]}"
    return Message(
        id=msg_id,
        conversation_id=conv_id,
        actor=ActorType.USER,
        timestamp=datetime(2025, 1, 1, 10, idx, tzinfo=timezone.utc),
        content_blob_uuid=f"blob-{idx:032d}"[:36],
    )


class TestVaultDB:
    def test_schema_creates_tables(self, db, tmp_path):
        assert (tmp_path / "test.db").exists()

    def test_add_and_count_conversation(self, db):
        conv = _make_conversation(1)
        db.add_conversation(conv, [])
        assert db.get_conversation_count() == 1

    def test_conversation_exists_by_hash(self, db):
        conv = _make_conversation(1)
        db.add_conversation(conv, [])
        assert db.conversation_exists(conv.hash)
        assert not db.conversation_exists("nonexistent-hash")

    def test_get_conversation_by_id(self, db):
        conv = _make_conversation(2)
        db.add_conversation(conv, [])
        fetched = db.get_conversation(conv.id)
        assert fetched is not None
        assert fetched.title == conv.title

    def test_get_conversation_returns_none_for_unknown(self, db):
        assert db.get_conversation("does-not-exist") is None

    def test_list_conversations_returns_all(self, db):
        for i in range(1, 6):
            db.add_conversation(_make_conversation(i), [])
        convs = db.list_conversations(limit=100)
        assert len(convs) == 5

    def test_list_conversations_pagination(self, db):
        for i in range(1, 11):
            db.add_conversation(_make_conversation(i), [])
        page1 = db.list_conversations(limit=5, offset=0)
        page2 = db.list_conversations(limit=5, offset=5)
        assert len(page1) == 5
        assert len(page2) == 5
        ids1 = {c.id for c in page1}
        ids2 = {c.id for c in page2}
        assert ids1.isdisjoint(ids2)

    def test_list_conversations_filter_by_source(self, db):
        db.add_conversation(_make_conversation(1, source="chatgpt"), [])
        db.add_conversation(_make_conversation(2, source="claude"), [])
        chatgpt_convs = db.list_conversations(source="chatgpt")
        assert len(chatgpt_convs) == 1
        assert chatgpt_convs[0].source == "chatgpt"

    def test_add_conversation_with_messages(self, db):
        conv = _make_conversation(1)
        msgs = [_make_message(conv.id, i) for i in range(1, 4)]
        db.add_conversation(conv, msgs)
        assert db.get_message_count() == 3

    def test_get_messages_ordered_by_timestamp(self, db):
        conv = _make_conversation(1)
        msgs = [_make_message(conv.id, i) for i in range(1, 4)]
        db.add_conversation(conv, msgs)
        fetched = db.get_messages(conv.id)
        assert len(fetched) == 3
        timestamps = [m.timestamp for m in fetched]
        assert timestamps == sorted(timestamps)

    def test_get_source_breakdown(self, db):
        db.add_conversation(_make_conversation(1, source="chatgpt"), [])
        db.add_conversation(_make_conversation(2, source="chatgpt"), [])
        db.add_conversation(_make_conversation(3, source="claude"), [])
        breakdown = db.get_source_breakdown()
        assert len(breakdown) == 2
        sources = {s: c for s, c in breakdown}
        assert sources["chatgpt"] == 2
        assert sources["claude"] == 1

    def test_get_date_range_empty(self, db):
        oldest, newest = db.get_date_range()
        assert oldest is None
        assert newest is None

    def test_get_date_range_with_data(self, db):
        db.add_conversation(_make_conversation(1), [])
        db.add_conversation(_make_conversation(5), [])
        oldest, newest = db.get_date_range()
        assert oldest is not None
        assert newest is not None
        assert oldest <= newest

    def test_duplicate_hash_raises(self, db):
        conv1 = _make_conversation(1)
        conv2 = _make_conversation(2)
        conv2.hash = conv1.hash  # force duplicate
        db.add_conversation(conv1, [])
        import sqlalchemy.exc
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db.add_conversation(conv2, [])
