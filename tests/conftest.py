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
