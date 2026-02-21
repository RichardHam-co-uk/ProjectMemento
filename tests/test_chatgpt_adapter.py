"""Tests for vault.ingestion.chatgpt (ChatGPTAdapter)."""
import json
from pathlib import Path

import pytest

from vault.ingestion.chatgpt import ChatGPTAdapter


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_chatgpt_export.json"


class TestChatGPTAdapter:
    """Test suite for ChatGPTAdapter."""

    def test_placeholder(self) -> None:
        """Placeholder test — always passes."""
        assert True

    def test_provider_name(self) -> None:
        """provider_name returns 'chatgpt'."""
        adapter = ChatGPTAdapter()
        assert adapter.provider_name == "chatgpt"

    # ------------------------------------------------------------------
    # validate_format
    # ------------------------------------------------------------------

    def test_validate_format_valid_fixture(self) -> None:
        """validate_format returns True for the sample fixture."""
        adapter = ChatGPTAdapter()
        assert adapter.validate_format(FIXTURE_PATH) is True

    def test_validate_format_rejects_non_json(self, tmp_path: Path) -> None:
        """validate_format returns False for non-JSON files."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json at all!!")
        adapter = ChatGPTAdapter()
        assert adapter.validate_format(bad_file) is False

    def test_validate_format_rejects_json_object(self, tmp_path: Path) -> None:
        """validate_format returns False when top-level is an object, not an array."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text('{"key": "value"}')
        adapter = ChatGPTAdapter()
        assert adapter.validate_format(bad_file) is False

    def test_validate_format_rejects_array_without_mapping(self, tmp_path: Path) -> None:
        """validate_format returns False when array items lack 'mapping'."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text('[{"title": "No mapping here"}]')
        adapter = ChatGPTAdapter()
        assert adapter.validate_format(bad_file) is False

    def test_validate_format_accepts_empty_array(self, tmp_path: Path) -> None:
        """validate_format accepts an empty array (empty export)."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("[]")
        adapter = ChatGPTAdapter()
        assert adapter.validate_format(empty_file) is True

    # ------------------------------------------------------------------
    # parse — happy path
    # ------------------------------------------------------------------

    def test_parse_fixture_returns_one_conversation(self) -> None:
        """Parsing the sample fixture returns exactly one conversation."""
        adapter = ChatGPTAdapter()
        convs = adapter.parse(FIXTURE_PATH)
        assert len(convs) == 1

    def test_parse_fixture_title(self) -> None:
        """Parsed conversation has the correct title."""
        adapter = ChatGPTAdapter()
        conv = adapter.parse(FIXTURE_PATH)[0]
        assert conv.title == "Test Conversation"

    def test_parse_fixture_source(self) -> None:
        """Parsed conversation has source == 'chatgpt'."""
        adapter = ChatGPTAdapter()
        conv = adapter.parse(FIXTURE_PATH)[0]
        assert conv.source == "chatgpt"

    def test_parse_fixture_external_id(self) -> None:
        """Parsed conversation carries the conversation_id as external_id."""
        adapter = ChatGPTAdapter()
        conv = adapter.parse(FIXTURE_PATH)[0]
        assert conv.external_id == "test-conv-001"

    def test_parse_fixture_two_messages(self) -> None:
        """Fixture with user + assistant yields exactly 2 messages."""
        adapter = ChatGPTAdapter()
        conv = adapter.parse(FIXTURE_PATH)[0]
        assert len(conv.messages) == 2

    def test_parse_fixture_message_actors(self) -> None:
        """Messages have the correct actors in chronological order."""
        adapter = ChatGPTAdapter()
        conv = adapter.parse(FIXTURE_PATH)[0]
        actors = [m.actor for m in conv.messages]
        assert actors == ["user", "assistant"]

    def test_parse_fixture_message_content(self) -> None:
        """User message content matches the fixture value."""
        adapter = ChatGPTAdapter()
        conv = adapter.parse(FIXTURE_PATH)[0]
        user_msg = next(m for m in conv.messages if m.actor == "user")
        assert "Hello" in user_msg.content

    def test_parse_fixture_assistant_metadata(self) -> None:
        """Assistant message carries model_slug in metadata."""
        adapter = ChatGPTAdapter()
        conv = adapter.parse(FIXTURE_PATH)[0]
        asst_msg = next(m for m in conv.messages if m.actor == "assistant")
        assert asst_msg.metadata.get("model_slug") == "gpt-4"

    # ------------------------------------------------------------------
    # Tree flattening
    # ------------------------------------------------------------------

    def test_tree_flattening_skip_null_messages(self, tmp_path: Path) -> None:
        """Nodes with null message fields are skipped during tree traversal."""
        data = [
            {
                "title": "Tree Test",
                "create_time": 1700000000.0,
                "update_time": 1700000100.0,
                "conversation_id": "tree-conv",
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
                            "content": {"content_type": "text", "parts": ["Hi"]},
                            "create_time": 1700000010.0,
                            "metadata": {},
                        },
                        "parent": "root",
                        "children": [],
                    },
                },
            }
        ]
        f = tmp_path / "conv.json"
        f.write_text(json.dumps(data))
        adapter = ChatGPTAdapter()
        convs = adapter.parse(f)
        assert len(convs) == 1
        assert len(convs[0].messages) == 1
        assert convs[0].messages[0].actor == "user"

    def test_tree_flattening_skips_unknown_roles(self, tmp_path: Path) -> None:
        """Messages with unknown roles (e.g. 'tool') are skipped."""
        data = [
            {
                "title": "Role Test",
                "create_time": 1700000000.0,
                "update_time": 1700000100.0,
                "conversation_id": "role-conv",
                "mapping": {
                    "msg1": {
                        "id": "msg1",
                        "message": {
                            "id": "msg1",
                            "author": {"role": "tool"},  # unknown role
                            "content": {"content_type": "text", "parts": ["output"]},
                            "create_time": 1700000010.0,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    },
                },
            }
        ]
        f = tmp_path / "conv.json"
        f.write_text(json.dumps(data))
        adapter = ChatGPTAdapter()
        convs = adapter.parse(f)
        assert len(convs[0].messages) == 0

    def test_tree_flattening_chronological_order(self, tmp_path: Path) -> None:
        """Messages are sorted in chronological order regardless of mapping order."""
        data = [
            {
                "title": "Order Test",
                "create_time": 1700000000.0,
                "update_time": 1700000100.0,
                "conversation_id": "order-conv",
                "mapping": {
                    "msg2": {
                        "id": "msg2",
                        "message": {
                            "id": "msg2",
                            "author": {"role": "assistant"},
                            "content": {"content_type": "text", "parts": ["Second"]},
                            "create_time": 1700000020.0,
                            "metadata": {},
                        },
                        "parent": "msg1",
                        "children": [],
                    },
                    "msg1": {
                        "id": "msg1",
                        "message": {
                            "id": "msg1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["First"]},
                            "create_time": 1700000010.0,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": ["msg2"],
                    },
                },
            }
        ]
        f = tmp_path / "conv.json"
        f.write_text(json.dumps(data))
        adapter = ChatGPTAdapter()
        conv = adapter.parse(f)[0]
        assert conv.messages[0].actor == "user"
        assert conv.messages[1].actor == "assistant"

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_parse_empty_export(self, tmp_path: Path) -> None:
        """Parsing an empty JSON array returns an empty list."""
        f = tmp_path / "empty.json"
        f.write_text("[]")
        adapter = ChatGPTAdapter()
        assert adapter.parse(f) == []

    def test_parse_conversation_with_no_messages(self, tmp_path: Path) -> None:
        """A conversation with an empty mapping produces 0 messages."""
        data = [
            {
                "title": "Empty Conv",
                "create_time": 1700000000.0,
                "update_time": 1700000000.0,
                "conversation_id": "empty-conv",
                "mapping": {},
            }
        ]
        f = tmp_path / "conv.json"
        f.write_text(json.dumps(data))
        adapter = ChatGPTAdapter()
        convs = adapter.parse(f)
        assert len(convs) == 1
        assert convs[0].messages == []

    def test_parse_rejects_oversized_file(self, tmp_path: Path) -> None:
        """Files larger than 100 MB raise ValueError."""
        big_file = tmp_path / "big.json"
        big_file.write_bytes(b"x" * (101 * 1024 * 1024))
        adapter = ChatGPTAdapter()
        with pytest.raises(ValueError, match="too large"):
            adapter.parse(big_file)

    def test_parse_rejects_invalid_json(self, tmp_path: Path) -> None:
        """Files that are not valid JSON raise ValueError."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("this is not json {{{")
        adapter = ChatGPTAdapter()
        with pytest.raises(ValueError):
            adapter.parse(bad_file)

    def test_parse_skips_empty_content_parts(self, tmp_path: Path) -> None:
        """Messages with empty content parts are skipped."""
        data = [
            {
                "title": "Empty Parts",
                "create_time": 1700000000.0,
                "update_time": 1700000000.0,
                "conversation_id": "empty-parts",
                "mapping": {
                    "msg1": {
                        "id": "msg1",
                        "message": {
                            "id": "msg1",
                            "author": {"role": "user"},
                            "content": {"content_type": "text", "parts": ["   "]},
                            "create_time": 1700000010.0,
                            "metadata": {},
                        },
                        "parent": None,
                        "children": [],
                    }
                },
            }
        ]
        f = tmp_path / "conv.json"
        f.write_text(json.dumps(data))
        adapter = ChatGPTAdapter()
        conv = adapter.parse(f)[0]
        # whitespace-only parts are skipped
        assert len(conv.messages) == 0

    def test_missing_title_defaults_to_untitled(self, tmp_path: Path) -> None:
        """Conversations without a title default to 'Untitled'."""
        data = [
            {
                "create_time": 1700000000.0,
                "update_time": 1700000000.0,
                "conversation_id": "no-title",
                "mapping": {},
            }
        ]
        f = tmp_path / "conv.json"
        f.write_text(json.dumps(data))
        adapter = ChatGPTAdapter()
        conv = adapter.parse(f)[0]
        assert conv.title == "Untitled"
