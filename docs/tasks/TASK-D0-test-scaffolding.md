# Task D0: Test Directory Scaffolding

**Target directory:** `tests/`
**Recommended model:** Llama3b or Qwen2.5-Coder (local)
**Effort:** Small (~15-20 min)
**Dependencies:** None

---

## Context

The LLM Memory Vault project has zero test files. We need pytest scaffolding — a conftest with shared fixtures and empty test files for every module that will be built.

## Requirements

Create these files:

### 1. `tests/__init__.py`
Empty file.

### 2. `tests/conftest.py`
```python
"""Shared pytest fixtures for the LLM Memory Vault test suite."""
import pytest
from pathlib import Path


@pytest.fixture
def tmp_vault_path(tmp_path: Path) -> Path:
    """Create a temporary vault directory for testing."""
    vault_dir = tmp_path / "test_vault"
    vault_dir.mkdir()
    (vault_dir / "blobs").mkdir()
    return vault_dir


@pytest.fixture
def sample_passphrase() -> str:
    """Return a valid test passphrase (>= 12 chars)."""
    return "test-passphrase-secure-12!"


@pytest.fixture
def weak_passphrase() -> str:
    """Return a passphrase that is too short."""
    return "short"
```

### 3. Empty Test Files (one per module)

Each file should have:
- A module docstring
- The correct imports (even if the module doesn't exist yet — just comment them out)
- One placeholder test that passes

Create these files:
- `tests/test_crypto.py` — "Tests for vault.security.crypto (KeyManager)"
- `tests/test_blobs.py` — "Tests for vault.storage.blobs (BlobStore)"
- `tests/test_migrations.py` — "Tests for vault.storage.migrations"
- `tests/test_db.py` — "Tests for vault.storage.db (VaultDB)"
- `tests/test_base_adapter.py` — "Tests for vault.ingestion.base"
- `tests/test_chatgpt_adapter.py` — "Tests for vault.ingestion.chatgpt (ChatGPTAdapter)"
- `tests/test_pipeline.py` — "Tests for vault.ingestion.pipeline (ImportPipeline)"
- `tests/test_session.py` — "Tests for vault.security.session (SessionManager)"
- `tests/test_cli.py` — "Tests for vault.cli.main (CLI commands)"

**Template for each:**
```python
"""Tests for vault.module.name."""


class TestClassName:
    """Test suite for ClassName."""

    def test_placeholder(self) -> None:
        """Placeholder test — replace with real tests."""
        assert True
```

### 4. `tests/fixtures/` directory
Create `tests/fixtures/sample_chatgpt_export.json` with a minimal valid ChatGPT export:

```json
[
  {
    "title": "Test Conversation",
    "create_time": 1700000000.0,
    "update_time": 1700000100.0,
    "conversation_id": "test-conv-001",
    "mapping": {
      "msg-root": {
        "id": "msg-root",
        "message": null,
        "parent": null,
        "children": ["msg-001"]
      },
      "msg-001": {
        "id": "msg-001",
        "message": {
          "id": "msg-001",
          "author": {"role": "user"},
          "content": {"content_type": "text", "parts": ["Hello, how are you?"]},
          "create_time": 1700000010.0,
          "metadata": {}
        },
        "parent": "msg-root",
        "children": ["msg-002"]
      },
      "msg-002": {
        "id": "msg-002",
        "message": {
          "id": "msg-002",
          "author": {"role": "assistant"},
          "content": {"content_type": "text", "parts": ["I'm doing well, thank you!"]},
          "create_time": 1700000020.0,
          "metadata": {"model_slug": "gpt-4"}
        },
        "parent": "msg-001",
        "children": []
      }
    }
  }
]
```

## Conventions
- Google-style docstrings
- Type hints on fixture return types
- Use `tmp_path` (built-in pytest fixture) as base for temporary directories

## Acceptance Criteria
- [ ] `poetry run pytest tests/ -v` runs and all placeholder tests pass
- [ ] conftest.py fixtures work (tmp_vault_path creates directory)
- [ ] Sample fixture JSON is valid JSON

---

## Console Prompt

```
Create the test scaffolding for the LLM Memory Vault project. Create tests/__init__.py (empty), tests/conftest.py with fixtures (tmp_vault_path using tmp_path, sample_passphrase, weak_passphrase), and empty test files for each module: test_crypto.py, test_blobs.py, test_migrations.py, test_db.py, test_base_adapter.py, test_chatgpt_adapter.py, test_pipeline.py, test_session.py, test_cli.py. Each test file should have a docstring, a test class, and one placeholder test that passes. Also create tests/fixtures/sample_chatgpt_export.json with a minimal valid ChatGPT export containing 1 conversation with 2 messages (user + assistant) in the mapping tree format.
```
