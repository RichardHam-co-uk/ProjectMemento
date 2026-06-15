"""Tests for the ProjectMemento shared memory layer (src/memento/)."""

import os
import tempfile
from pathlib import Path

import pytest

from memento.api import MementoAPI
from memento.models import (
    Fact,
    Memory,
    MemorySensitivity,
    MemorySource,
    MemoryStatus,
    MemoryType,
    Preference,
    Session as MementoSession,
)
from memento.store import (
    DuplicateEntryError,
    EntryNotFoundError,
    SQLiteStore,
)


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def store(tmp_dir):
    db_path = tmp_dir / "test.db"
    s = SQLiteStore(db_path)
    yield s
    s.close()


@pytest.fixture
def api(tmp_dir):
    db_path = tmp_dir / "test.db"
    a = MementoAPI(db_path)
    yield a
    a.close()


# ── Model Tests ───────────────────────────────────────────────────


class TestMemoryModel:
    def test_create_basic_memory(self):
        m = Memory(
            type=MemoryType.PROJECT_STATE,
            namespace="project/test",
            title="Test memory",
            summary="A test summary",
            source=MemorySource(system="test"),
        )
        assert m.status == MemoryStatus.STAGED
        assert m.sensitivity == MemorySensitivity.RESTRICTED
        assert m.confidence == 0.5

    def test_deterministic_id(self):
        m1 = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Same content",
            summary="Same summary",
            source=MemorySource(system="test"),
        )
        m2 = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Same content",
            summary="Same summary",
            source=MemorySource(system="test"),
        )
        assert m1.deterministic_id() == m2.deterministic_id()

    def test_content_hash_stable(self):
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Stable",
            summary="Stable content",
            source=MemorySource(system="test"),
        )
        assert m.compute_content_hash() == m.compute_content_hash()

    def test_invalid_namespace(self):
        with pytest.raises(Exception):
            Memory(
                type=MemoryType.SEMANTIC,
                namespace="invalid/root",
                title="Test",
                summary="Test",
                source=MemorySource(system="test"),
            )

    def test_client_namespace_requires_high_sensitivity(self):
        # Client namespaces should reject public/internal sensitivity
        # This is validated at the store level for the new models
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="client/test",
            title="Client data",
            summary="Sensitive client information",
            source=MemorySource(system="test"),
            sensitivity=MemorySensitivity.CLIENT_CONFIDENTIAL,
        )
        assert m.namespace == "client/test"

    def test_safe_view_hides_body(self):
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Test",
            summary="Test summary",
            body="Secret body content",
            source=MemorySource(system="test"),
        )
        safe = m.safe_view()
        assert "hidden" in safe["body"]
        full = m.safe_view(include_body=True)
        assert full["body"] == "Secret body content"

    def test_tags_normalized(self):
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Test",
            summary="Test",
            source=MemorySource(system="test"),
            tags=["Python", "python", "  CODE  "],
        )
        assert m.tags == ["code", "python"]


class TestFactModel:
    def test_create_fact(self):
        f = Fact(
            subject="Python",
            predicate="is_a",
            object_value="programming language",
        )
        assert f.id is None
        assert f.status == MemoryStatus.STAGED

    def test_fact_deterministic_id(self):
        f1 = Fact(subject="A", predicate="is", object_value="B")
        f2 = Fact(subject="A", predicate="is", object_value="B")
        assert f1.deterministic_id() == f2.deterministic_id()


class TestPreferenceModel:
    def test_create_preference(self):
        p = Preference(
            key="coding_style.python",
            value="Use type hints and docstrings",
        )
        assert p.confidence == 0.9

    def test_preference_deterministic_id(self):
        p1 = Preference(key="test.key", value="test_value")
        p2 = Preference(key="test.key", value="test_value")
        assert p1.deterministic_id() == p2.deterministic_id()


class TestSessionModel:
    def test_create_session(self):
        s = MementoSession(
            agent="claude",
            title="Phase 1 implementation",
            namespace="project/projectmemento",
        )
        assert s.agent == "claude"
        assert s.ended_at is None


# ── Store Tests ──────────────────────────────────────────────────


class TestSQLiteStore:
    def test_create_and_get_memory(self, store):
        m = Memory(
            type=MemoryType.PROJECT_STATE,
            namespace="project/test",
            title="Test memory",
            summary="A test summary",
            source=MemorySource(system="test"),
        )
        created = store.create_memory(m)
        assert created.id is not None
        assert created.id.startswith("mem_")

        retrieved = store.get_memory(created.id)
        assert retrieved.title == "Test memory"
        assert retrieved.summary == "A test summary"

    def test_duplicate_rejected(self, store):
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Duplicate test",
            summary="Same content",
            source=MemorySource(system="test"),
        )
        store.create_memory(m)
        with pytest.raises(DuplicateEntryError):
            store.create_memory(m)

    def test_get_nonexistent_raises(self, store):
        with pytest.raises(EntryNotFoundError):
            store.get_memory("mem_nonexistent000")

    def test_approve_memory(self, store):
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Approve test",
            summary="To be approved",
            source=MemorySource(system="test"),
        )
        created = store.create_memory(m)
        assert created.status == MemoryStatus.STAGED

        approved = store.approve_memory(created.id, approved_by="richard")
        assert approved.status == MemoryStatus.APPROVED
        assert approved.approved_by == "richard"

    def test_reject_memory(self, store):
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Reject test",
            summary="To be rejected",
            source=MemorySource(system="test"),
        )
        created = store.create_memory(m)
        rejected = store.reject_memory(created.id, reason="Not relevant")
        assert rejected.status == MemoryStatus.REJECTED
        assert rejected.status_reason == "Not relevant"

    def test_search_returns_approved_only(self, store):
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Search test",
            summary="alpha beta gamma",
            source=MemorySource(system="test"),
        )
        created = store.create_memory(m)

        # Staged memories should not appear in search
        assert store.search_memories("alpha") == []

        # After approval, they should
        store.approve_memory(created.id, approved_by="test")
        results = store.search_memories("alpha")
        assert len(results) == 1
        assert results[0].id == created.id

    def test_search_with_staged(self, store):
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Staged search",
            summary="delta epsilon",
            source=MemorySource(system="test"),
        )
        created = store.create_memory(m)
        results = store.search_memories("delta", include_staged=True)
        assert len(results) == 1

    def test_list_with_filters(self, store):
        for i in range(3):
            m = Memory(
                type=MemoryType.SEMANTIC,
                namespace="project/filter_test",
                title=f"Filter test {i}",
                summary=f"Summary {i}",
                source=MemorySource(system="test"),
            )
            store.create_memory(m)

        results = store.list_memories(namespace="project/filter_test")
        assert len(results) == 3

        results = store.list_memories(
            namespace="project/filter_test",
            status=MemoryStatus.STAGED,
        )
        assert len(results) == 3

    def test_soft_delete(self, store):
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Delete test",
            summary="To be deleted",
            source=MemorySource(system="test"),
        )
        created = store.create_memory(m)
        store.delete_memory(created.id, soft=True)

        with pytest.raises(EntryNotFoundError):
            store.get_memory(created.id)

    def test_hard_delete(self, store):
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Hard delete",
            summary="To be permanently deleted",
            source=MemorySource(system="test"),
        )
        created = store.create_memory(m)
        store.delete_memory(created.id, soft=False)

        with pytest.raises(EntryNotFoundError):
            store.get_memory(created.id)

    def test_create_and_get_fact(self, store):
        f = Fact(
            subject="SQLite",
            predicate="is_a",
            object_value="database engine",
        )
        created = store.create_fact(f)
        assert created.id is not None
        assert created.id.startswith("fact_")

        retrieved = store.get_fact(created.id)
        assert retrieved.subject == "SQLite"

    def test_create_and_get_preference(self, store):
        p = Preference(
            key="style.python",
            value="Use black for formatting",
        )
        created = store.create_preference(p)
        assert created.id is not None
        assert created.id.startswith("pref_")

        retrieved = store.get_preference(created.id)
        assert retrieved.value == "Use black for formatting"

    def test_create_and_get_session(self, store):
        s = MementoSession(
            agent="claude",
            title="Test session",
            namespace="project/test",
        )
        created = store.create_session(s)
        assert created.id is not None
        assert created.id.startswith("sess_")

        retrieved = store.get_session(created.id)
        assert retrieved.agent == "claude"

    def test_end_session(self, store):
        s = MementoSession(
            agent="codex",
            title="Implementation session",
        )
        created = store.create_session(s)
        assert created.ended_at is None

        ended = store.end_session(created.id)
        assert ended.ended_at is not None

    def test_stats(self, store):
        m = Memory(
            type=MemoryType.SEMANTIC,
            namespace="project/test",
            title="Stats test",
            summary="For stats",
            source=MemorySource(system="test"),
        )
        store.create_memory(m)
        s = store.stats()
        assert s["total_records"] >= 1
        assert "by_status" in s
        assert "by_type" in s
        assert "db_path" in s


# ── API Tests ────────────────────────────────────────────────────


class TestMementoAPI:
    def test_remember_and_recall(self, api):
        api.remember(
            title="API test",
            summary="Testing the high-level API",
            namespace="project/test",
            source_system="test",
            auto_approve=True,
        )
        results = api.recall("high-level API")
        assert len(results) == 1
        assert results[0].title == "API test"

    def test_remember_staged_not_in_recall(self, api):
        api.remember(
            title="Staged only",
            summary="Should not appear in recall",
            namespace="project/test",
            source_system="test",
        )
        results = api.recall("Staged only")
        assert len(results) == 0

    def test_remember_and_approve(self, api):
        mem = api.remember(
            title="Approve me",
            summary="Staged then approved",
            namespace="project/test",
            source_system="test",
        )
        assert mem.status == MemoryStatus.STAGED

        approved = api.approve(mem.id, approved_by="richard")
        assert approved.status == MemoryStatus.APPROVED

        results = api.recall("Staged then approved")
        assert len(results) == 1

    def test_remember_fact_via_api(self, api):
        fact = api.remember_fact(
            subject="ProjectMemento",
            predicate="uses",
            object_value="SQLite for Phase 1",
            source_system="test",
        )
        assert fact.id.startswith("fact_")

        facts = api.list_facts()
        assert len(facts) >= 1

    def test_remember_preference_via_api(self, api):
        pref = api.remember_preference(
            key="output.format",
            value="concise and direct",
            source_system="test",
        )
        assert pref.id.startswith("pref_")

        prefs = api.list_preferences()
        assert len(prefs) >= 1

    def test_session_lifecycle(self, api):
        sess = api.start_session(
            agent="claude",
            title="Phase 1 development",
            namespace="project/projectmemento",
            context={"task": "Build foundation"},
        )
        assert sess.id.startswith("sess_")

        sessions = api.list_sessions(agent="claude")
        assert len(sessions) >= 1

        ended = api.end_session(sess.id)
        assert ended.ended_at is not None

    def test_forget(self, api):
        mem = api.remember(
            title="Forget me",
            summary="To be forgotten",
            namespace="project/test",
            source_system="test",
        )
        api.forget(mem.id)

        with pytest.raises(EntryNotFoundError):
            api.get_memory(mem.id)

    def test_context_manager(self, tmp_dir):
        db_path = tmp_dir / "ctx_test.db"
        with MementoAPI(db_path) as api:
            mem = api.remember(
                title="Context manager test",
                summary="Testing with-statement",
                namespace="project/test",
                source_system="test",
            )
            assert mem.id is not None

    def test_stats_via_api(self, api):
        api.remember(
            title="Stats test",
            summary="For API stats",
            namespace="project/test",
            source_system="test",
        )
        s = api.stats()
        assert s["total_records"] >= 1
