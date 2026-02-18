"""
Unit tests for vault.ingestion.chatgpt (ChatGPTAdapter).
"""
import json
import pytest
from pathlib import Path

from vault.ingestion.chatgpt import ChatGPTAdapter


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_chatgpt_export.json"


@pytest.fixture
def adapter() -> ChatGPTAdapter:
    return ChatGPTAdapter()


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    """Copy fixture to tmp_path to keep tests isolated."""
    import shutil
    dest = tmp_path / "conversations.json"
    shutil.copy(FIXTURE_PATH, dest)
    return dest


class TestValidateFormat:
    def test_valid_export_returns_true(self, adapter, sample_file):
        assert adapter.validate_format(sample_file) is True

    def test_empty_array_is_invalid(self, adapter, tmp_path):
        # Adapter requires at least one element with a 'mapping' key
        f = tmp_path / "empty.json"
        f.write_text("[]")
        assert adapter.validate_format(f) is False

    def test_non_json_returns_false(self, adapter, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("this is not json at all")
        assert adapter.validate_format(f) is False

    def test_missing_file_returns_false(self, adapter, tmp_path):
        assert adapter.validate_format(tmp_path / "nonexistent.json") is False

    def test_json_object_instead_of_array_returns_false(self, adapter, tmp_path):
        f = tmp_path / "obj.json"
        f.write_text('{"key": "value"}')
        assert adapter.validate_format(f) is False


class TestParse:
    def test_parses_correct_number_of_conversations(self, adapter, sample_file):
        parsed = adapter.parse(sample_file)
        assert len(parsed) == 2

    def test_conversation_has_correct_title(self, adapter, sample_file):
        parsed = adapter.parse(sample_file)
        titles = {c.title for c in parsed}
        assert "Python Async Basics" in titles
        assert "SQLAlchemy Tips" in titles

    def test_conversation_has_messages(self, adapter, sample_file):
        parsed = adapter.parse(sample_file)
        for conv in parsed:
            assert len(conv.messages) >= 2

    def test_message_actors(self, adapter, sample_file):
        parsed = adapter.parse(sample_file)
        conv = next(c for c in parsed if c.title == "Python Async Basics")
        actors = [m.actor for m in conv.messages]
        assert "user" in actors
        assert "assistant" in actors

    def test_message_content_not_empty(self, adapter, sample_file):
        parsed = adapter.parse(sample_file)
        for conv in parsed:
            for msg in conv.messages:
                assert msg.content.strip()

    def test_message_timestamps_present(self, adapter, sample_file):
        parsed = adapter.parse(sample_file)
        for conv in parsed:
            for msg in conv.messages:
                assert msg.timestamp is not None

    def test_conversation_hash_is_consistent(self, adapter, sample_file):
        parsed1 = adapter.parse(sample_file)
        parsed2 = adapter.parse(sample_file)
        hashes1 = {c.content_hash for c in parsed1}
        hashes2 = {c.content_hash for c in parsed2}
        assert hashes1 == hashes2

    def test_empty_export_returns_empty_list(self, adapter, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("[]")
        parsed = adapter.parse(f)
        assert parsed == []

    def test_conversation_with_null_messages_handled(self, adapter, tmp_path):
        """Conversations with null message nodes should not crash the parser."""
        data = [
            {
                "title": "Sparse Conv",
                "create_time": 1707300000.0,
                "update_time": 1707300000.0,
                "mapping": {
                    "root": {
                        "id": "root",
                        "message": None,
                        "parent": None,
                        "children": ["msg1"],
                    },
                    "msg1": {
                        "id": "msg1",
                        "message": {
                            "id": "msg1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["hello"]},
                            "create_time": 1707300010.0,
                            "metadata": {},
                        },
                        "parent": "root",
                        "children": [],
                    },
                },
            }
        ]
        f = tmp_path / "sparse.json"
        f.write_text(json.dumps(data))
        parsed = adapter.parse(f)
        assert len(parsed) == 1
        assert len(parsed[0].messages) == 1

    def test_provider_name(self, adapter):
        assert adapter.provider_name == "chatgpt"
