# Task T-test-cli: Real Tests for CLI Commands

**Target file:** `tests/test_cli.py` (replace placeholder)
**Recommended model:** Qwen2.5-Coder or GPT-4o-mini
**Effort:** Medium (~2 hours)
**Dependencies:** All CLI commands must exist in `vault/cli/main.py`

---

## Context

`tests/test_cli.py` currently has a single `test_placeholder`. Replace it with
a real test suite that invokes the CLI via Typer's `CliRunner`.

## Files to Read First

- `vault/cli/main.py` — full file (all commands)
- `vault/storage/db.py` — VaultDB (to set up pre-existing vault state)

## Test Infrastructure

Use `typer.testing.CliRunner` — it invokes the app in-process without spawning
subprocesses:

```python
from typer.testing import CliRunner
from vault.cli.main import app

runner = CliRunner()

def invoke(*args, input=None):
    """Helper: invoke CLI and return result."""
    return runner.invoke(app, list(args), input=input)
```

## Fixtures

```python
import pytest
from pathlib import Path
from vault.storage.db import VaultDB

@pytest.fixture
def vault_dir(tmp_path):
    """Create a minimal initialised vault directory for tests."""
    vault_path = tmp_path / "vault_data"
    vault_path.mkdir()
    (vault_path / "blobs").mkdir()
    db = VaultDB(vault_path / "vault.db")
    db.init_schema()
    return vault_path
```

## Tests to Write

```python
class TestCLI:

    # --- version ---

    def test_version(self):
        result = invoke("version")
        assert result.exit_code == 0
        assert "v0.1.0" in result.output or "Vault" in result.output

    # --- list ---

    def test_list_no_vault(self, tmp_path):
        """list should exit 1 when vault does not exist."""
        result = invoke("list", "--vault-path", str(tmp_path / "nonexistent"))
        assert result.exit_code == 1
        assert "init" in result.output.lower() or "not" in result.output.lower()

    def test_list_empty_vault(self, vault_dir):
        result = invoke("list", "--vault-path", str(vault_dir))
        assert result.exit_code == 0
        assert "No conversations" in result.output or result.output.strip() != ""

    # --- stats ---

    def test_stats_no_vault(self, tmp_path):
        result = invoke("stats", "--vault-path", str(tmp_path / "nonexistent"))
        assert result.exit_code == 1

    def test_stats_empty_vault(self, vault_dir):
        result = invoke("stats", "--vault-path", str(vault_dir))
        assert result.exit_code == 0
        assert "0" in result.output  # 0 conversations

    # --- show ---

    def test_show_no_vault(self, tmp_path):
        result = invoke("show", "abc12345", "--vault-path", str(tmp_path / "nonexistent"))
        assert result.exit_code == 1

    def test_show_nonexistent_id(self, vault_dir):
        result = invoke("show", "deadbeef", "--vault-path", str(vault_dir))
        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "No conversation" in result.output

    # --- lock ---

    def test_lock_no_active_session(self, vault_dir):
        """lock should not raise even if no session exists."""
        result = invoke("lock", "--vault-path", str(vault_dir))
        assert result.exit_code == 0

    # --- import chatgpt ---

    def test_import_chatgpt_file_not_found(self, vault_dir):
        result = invoke("import", "chatgpt", str(vault_dir / "ghost.json"),
                        "--vault-path", str(vault_dir))
        assert result.exit_code == 1

    def test_import_chatgpt_no_vault(self, tmp_path):
        result = invoke("import", "chatgpt", str(tmp_path / "file.json"),
                        "--vault-path", str(tmp_path / "nonexistent"))
        assert result.exit_code == 1

    def test_import_chatgpt_invalid_format(self, tmp_path, vault_dir):
        bad = tmp_path / "bad.json"
        bad.write_text('[{"not_chatgpt": true}]')
        result = invoke("import", "chatgpt", str(bad),
                        "--vault-path", str(vault_dir))
        assert result.exit_code == 1
```

## Conventions

- Use `typer.testing.CliRunner` — **not** `subprocess`.
- Define `invoke()` helper and `vault_dir` fixture at module level.
- Remove `test_placeholder` entirely.
- Keep `TestCLI` class name.
- Tests should not test `vault init` — it prompts for a passphrase and
  triggers Argon2 (slow); use the `vault_dir` fixture instead to pre-build
  a vault.

---

## Console Prompt

```
Read vault/cli/main.py in full. Read vault/storage/db.py briefly.

Replace tests/test_cli.py with real CLI tests using typer.testing.CliRunner.
Define a module-level invoke() helper and a vault_dir fixture that manually
creates the vault directory structure and initialises the DB (bypassing the
init command to avoid prompts). Cover: version outputs version string, list
exits 1 for missing vault, list exits 0 for empty vault, stats exits 1 for
missing vault, stats exits 0 and shows 0 for empty vault, show exits 1 for
missing vault, show exits 1 for unknown id, lock exits 0 with no session,
import chatgpt exits 1 for missing file, exits 1 for missing vault, exits 1
for invalid format.

Remove test_placeholder. Keep TestCLI class name.
```
