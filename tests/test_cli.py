"""Tests for vault.cli.main (CLI commands)."""
import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vault.cli.main import app

runner = CliRunner()

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_chatgpt_export.json"


class TestCLIVersion:
    """Tests for the version command."""

    def test_version_exits_zero(self) -> None:
        """vault version exits with code 0."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0

    def test_version_output(self) -> None:
        """vault version prints the version string."""
        result = runner.invoke(app, ["version"])
        assert "0.1.0" in result.output


class TestCLIInit:
    """Tests for the vault init command."""

    def test_init_creates_vault(self, tmp_path: Path) -> None:
        """vault init creates the vault directory and salt file."""
        vault_dir = tmp_path / "myvault"
        passphrase = "test-passphrase-secure-12!"
        result = runner.invoke(
            app,
            ["init", "--vault-path", str(vault_dir)],
            input=f"{passphrase}\n{passphrase}\n",
        )
        assert result.exit_code == 0, result.output
        assert (vault_dir / ".salt").exists()
        assert (vault_dir / "vault.db").exists()
        assert (vault_dir / "blobs").is_dir()

    def test_init_refuses_overwrite_without_force(self, tmp_path: Path) -> None:
        """vault init refuses to reinitialise without --force."""
        vault_dir = tmp_path / "myvault"
        passphrase = "test-passphrase-secure-12!"

        # First init
        runner.invoke(
            app,
            ["init", "--vault-path", str(vault_dir)],
            input=f"{passphrase}\n{passphrase}\n",
        )

        # Second init without --force should fail
        result = runner.invoke(
            app,
            ["init", "--vault-path", str(vault_dir)],
            input=f"{passphrase}\n{passphrase}\n",
        )
        assert result.exit_code != 0

    def test_init_force_overwrites(self, tmp_path: Path) -> None:
        """vault init --force successfully reinitialises an existing vault."""
        vault_dir = tmp_path / "myvault"
        passphrase = "test-passphrase-secure-12!"

        runner.invoke(
            app,
            ["init", "--vault-path", str(vault_dir)],
            input=f"{passphrase}\n{passphrase}\n",
        )
        result = runner.invoke(
            app,
            ["init", "--force", "--vault-path", str(vault_dir)],
            input=f"{passphrase}\n{passphrase}\n",
        )
        assert result.exit_code == 0

    def test_init_rejects_short_passphrase(self, tmp_path: Path) -> None:
        """vault init loops until a valid passphrase is given."""
        vault_dir = tmp_path / "myvault"
        # Provide short passphrase first, then valid one
        passphrase_good = "test-passphrase-secure-12!"
        result = runner.invoke(
            app,
            ["init", "--vault-path", str(vault_dir)],
            # "short" fails, then valid passphrase is accepted
            input=f"short\n{passphrase_good}\n{passphrase_good}\n",
        )
        assert result.exit_code == 0

    def test_init_output_contains_session_token(self, tmp_path: Path) -> None:
        """vault init output contains VAULT_SESSION_TOKEN export hint."""
        vault_dir = tmp_path / "myvault"
        passphrase = "test-passphrase-secure-12!"
        result = runner.invoke(
            app,
            ["init", "--vault-path", str(vault_dir)],
            input=f"{passphrase}\n{passphrase}\n",
        )
        assert "VAULT_SESSION_TOKEN" in result.output


class TestCLIImport:
    """Tests for the vault import command."""

    def _init_vault(self, vault_dir: Path, passphrase: str) -> None:
        """Helper: initialise a vault (discards session token)."""
        result = runner.invoke(
            app,
            ["init", "--vault-path", str(vault_dir)],
            input=f"{passphrase}\n{passphrase}\n",
        )
        assert result.exit_code == 0, result.output

    def test_import_fixture_succeeds(self, tmp_path: Path) -> None:
        """vault import chatgpt <fixture> exits 0 and reports 1 imported."""
        vault_dir = tmp_path / "myvault"
        passphrase = "test-passphrase-secure-12!"
        self._init_vault(vault_dir, passphrase)

        # Pass passphrase via stdin for authentication
        result = runner.invoke(
            app,
            ["import", "chatgpt", str(FIXTURE_PATH), "--vault-path", str(vault_dir)],
            input=f"{passphrase}\n",
        )
        assert result.exit_code == 0, result.output
        assert "1" in result.output  # 1 imported

    def test_import_rejects_unknown_provider(self, tmp_path: Path) -> None:
        """vault import with an unknown provider exits non-zero."""
        vault_dir = tmp_path / "myvault"
        passphrase = "test-passphrase-secure-12!"
        self._init_vault(vault_dir, passphrase)

        result = runner.invoke(
            app,
            ["import", "fakeProvider", str(FIXTURE_PATH), "--vault-path", str(vault_dir)],
            input=f"{passphrase}\n",
        )
        assert result.exit_code != 0

    def test_import_rejects_missing_file(self, tmp_path: Path) -> None:
        """vault import with a non-existent file exits non-zero."""
        vault_dir = tmp_path / "myvault"
        passphrase = "test-passphrase-secure-12!"
        self._init_vault(vault_dir, passphrase)

        result = runner.invoke(
            app,
            [
                "import",
                "chatgpt",
                str(tmp_path / "nonexistent.json"),
                "--vault-path",
                str(vault_dir),
            ],
            input=f"{passphrase}\n",
        )
        assert result.exit_code != 0

    def test_import_without_vault_exits_nonzero(self, tmp_path: Path) -> None:
        """vault import fails gracefully when no vault exists."""
        result = runner.invoke(
            app,
            [
                "import",
                "chatgpt",
                str(FIXTURE_PATH),
                "--vault-path",
                str(tmp_path / "nonexistent_vault"),
            ],
        )
        assert result.exit_code != 0

    def test_import_dedup_second_run(self, tmp_path: Path) -> None:
        """Importing the same file twice shows 0 imported and 1 skipped."""
        vault_dir = tmp_path / "myvault"
        passphrase = "test-passphrase-secure-12!"
        self._init_vault(vault_dir, passphrase)

        args = ["import", "chatgpt", str(FIXTURE_PATH), "--vault-path", str(vault_dir)]

        runner.invoke(app, args, input=f"{passphrase}\n")
        result2 = runner.invoke(app, args, input=f"{passphrase}\n")
        assert result2.exit_code == 0, result2.output
        # 0 imported, 1 skipped
        assert "0" in result2.output
        assert "1" in result2.output


class TestCLIList:
    """Tests for the vault list command."""

    def test_list_empty_vault(self, tmp_path: Path) -> None:
        """vault list on an empty vault shows 'No conversations'."""
        vault_dir = tmp_path / "myvault"
        passphrase = "test-passphrase-secure-12!"
        runner.invoke(
            app,
            ["init", "--vault-path", str(vault_dir)],
            input=f"{passphrase}\n{passphrase}\n",
        )
        result = runner.invoke(app, ["list", "--vault-path", str(vault_dir)])
        assert result.exit_code == 0
        assert "No conversations" in result.output

    def test_list_without_vault_exits_nonzero(self, tmp_path: Path) -> None:
        """vault list fails gracefully when no vault exists."""
        result = runner.invoke(
            app,
            ["list", "--vault-path", str(tmp_path / "no_vault")],
        )
        assert result.exit_code != 0


class TestCLIStats:
    """Tests for the vault stats command."""

    def test_stats_empty_vault(self, tmp_path: Path) -> None:
        """vault stats on an empty vault exits 0."""
        vault_dir = tmp_path / "myvault"
        passphrase = "test-passphrase-secure-12!"
        runner.invoke(
            app,
            ["init", "--vault-path", str(vault_dir)],
            input=f"{passphrase}\n{passphrase}\n",
        )
        result = runner.invoke(app, ["stats", "--vault-path", str(vault_dir)])
        assert result.exit_code == 0
        assert "0" in result.output

    def test_stats_without_vault_exits_nonzero(self, tmp_path: Path) -> None:
        """vault stats fails gracefully when no vault exists."""
        result = runner.invoke(
            app,
            ["stats", "--vault-path", str(tmp_path / "no_vault")],
        )
        assert result.exit_code != 0
