"""Tests for vault.ingestion.pipeline (ImportPipeline)."""
from pathlib import Path

import pytest

from vault.ingestion.chatgpt import ChatGPTAdapter
from vault.ingestion.pipeline import ImportPipeline
from vault.security.crypto import KeyManager
from vault.storage.blobs import BlobStore
from vault.storage.db import VaultDB

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_chatgpt_export.json"


@pytest.fixture
def vault_components(tmp_vault_path: Path, sample_passphrase: str):
    """Return an initialized (db, blob_store, master_key) triple."""
    km = KeyManager(tmp_vault_path)
    master_key = km.derive_master_key(sample_passphrase)
    db_path = tmp_vault_path / "vault.db"
    db = VaultDB(db_path)
    db.init_schema()
    blob_store = BlobStore(tmp_vault_path / "blobs", km)
    return db, blob_store, master_key


class TestImportPipeline:
    """Test suite for ImportPipeline."""

    def test_placeholder(self) -> None:
        """Placeholder test — always passes."""
        assert True

    def test_import_fixture(self, vault_components) -> None:
        """Importing the sample fixture succeeds with 1 imported conversation."""
        db, blob_store, master_key = vault_components
        pipeline = ImportPipeline(db=db, blob_store=blob_store, master_key=master_key)
        adapter = ChatGPTAdapter()
        result = pipeline.import_conversations(adapter, FIXTURE_PATH)
        assert result.imported == 1
        assert result.skipped == 0
        assert result.failed == 0
        assert result.errors == []

    def test_import_persists_to_db(self, vault_components) -> None:
        """Imported conversations are persisted to the database."""
        db, blob_store, master_key = vault_components
        pipeline = ImportPipeline(db=db, blob_store=blob_store, master_key=master_key)
        adapter = ChatGPTAdapter()
        pipeline.import_conversations(adapter, FIXTURE_PATH)
        assert db.count_conversations() == 1
        assert db.count_messages() == 2

    def test_import_dedup_second_import_skipped(self, vault_components) -> None:
        """Importing the same file twice skips duplicates on second run."""
        db, blob_store, master_key = vault_components
        pipeline = ImportPipeline(db=db, blob_store=blob_store, master_key=master_key)
        adapter = ChatGPTAdapter()

        result1 = pipeline.import_conversations(adapter, FIXTURE_PATH)
        result2 = pipeline.import_conversations(adapter, FIXTURE_PATH)

        assert result1.imported == 1
        assert result2.imported == 0
        assert result2.skipped == 1
        # Database should still have exactly 1 conversation
        assert db.count_conversations() == 1

    def test_import_progress_callback(self, vault_components) -> None:
        """Progress callback is called for each conversation processed."""
        db, blob_store, master_key = vault_components
        pipeline = ImportPipeline(db=db, blob_store=blob_store, master_key=master_key)
        adapter = ChatGPTAdapter()

        calls: list[tuple[int, int]] = []

        def on_progress(current: int, total: int) -> None:
            calls.append((current, total))

        pipeline.import_conversations(adapter, FIXTURE_PATH, on_progress=on_progress)
        assert len(calls) == 1
        assert calls[0] == (1, 1)

    def test_import_source_counts(self, vault_components) -> None:
        """Source counts reflect the imported provider."""
        db, blob_store, master_key = vault_components
        pipeline = ImportPipeline(db=db, blob_store=blob_store, master_key=master_key)
        adapter = ChatGPTAdapter()
        pipeline.import_conversations(adapter, FIXTURE_PATH)
        counts = db.get_source_counts()
        assert counts.get("chatgpt") == 1

    def test_import_bad_file_returns_failed(self, vault_components, tmp_path: Path) -> None:
        """A missing or unparseable file increments the failed counter."""
        db, blob_store, master_key = vault_components
        pipeline = ImportPipeline(db=db, blob_store=blob_store, master_key=master_key)
        adapter = ChatGPTAdapter()

        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json!!!")
        result = pipeline.import_conversations(adapter, bad_file)
        assert result.failed == 1
        assert len(result.errors) == 1

    def test_import_blobs_encrypted(self, vault_components) -> None:
        """After import, blob files exist and can be decrypted."""
        db, blob_store, master_key = vault_components
        pipeline = ImportPipeline(db=db, blob_store=blob_store, master_key=master_key)
        adapter = ChatGPTAdapter()
        pipeline.import_conversations(adapter, FIXTURE_PATH)

        # With expire_on_commit=False, column attributes are accessible after session close
        convs = db.list_conversations()
        assert len(convs) == 1
        conv_id = convs[0].id  # column attribute, safe after session close

        messages = db.get_messages_for_conversation(conv_id)
        assert len(messages) == 2

        # Decrypt and verify content using eagerly-loaded column values
        for msg in messages:
            blob_uuid = msg.content_blob_uuid  # column attribute, safe after session close
            content = blob_store.retrieve(blob_uuid, master_key, conv_id)
            assert len(content) > 0
