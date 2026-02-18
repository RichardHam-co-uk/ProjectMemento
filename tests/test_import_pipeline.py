"""
Unit tests for vault.ingestion.pipeline (ImportPipeline).
"""
import pytest
from pathlib import Path

from vault.ingestion.chatgpt import ChatGPTAdapter
from vault.ingestion.pipeline import ImportPipeline
from vault.security.crypto import KeyManager
from vault.storage.blobs import BlobStore
from vault.storage.database import VaultDB


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_chatgpt_export.json"
PASSPHRASE = "pipeline-test-passphrase-456!"


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def key_manager(vault_root: Path) -> KeyManager:
    return KeyManager(vault_root)


@pytest.fixture
def master_key(key_manager: KeyManager) -> bytes:
    return key_manager.derive_master_key(PASSPHRASE)


@pytest.fixture
def db(vault_root: Path) -> VaultDB:
    vault_db = VaultDB(vault_root / "vault.db")
    vault_db.create_schema()
    return vault_db


@pytest.fixture
def blob_store(vault_root: Path, key_manager: KeyManager) -> BlobStore:
    return BlobStore(vault_root / "blobs", key_manager)


@pytest.fixture
def pipeline(db: VaultDB, blob_store: BlobStore, key_manager: KeyManager) -> ImportPipeline:
    return ImportPipeline(db, blob_store, key_manager)


@pytest.fixture
def adapter() -> ChatGPTAdapter:
    return ChatGPTAdapter()


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    import shutil
    dest = tmp_path / "conversations.json"
    shutil.copy(FIXTURE_PATH, dest)
    return dest


class TestImportPipeline:
    def test_basic_import_returns_result(self, pipeline, adapter, sample_file, master_key):
        result = pipeline.import_conversations(adapter, sample_file, master_key)
        assert result is not None

    def test_imports_correct_count(self, pipeline, adapter, sample_file, master_key):
        result = pipeline.import_conversations(adapter, sample_file, master_key)
        assert result.imported == 2
        assert result.skipped == 0
        assert result.failed == 0

    def test_conversations_persisted_to_db(self, pipeline, adapter, sample_file, master_key, db):
        pipeline.import_conversations(adapter, sample_file, master_key)
        assert db.get_conversation_count() == 2

    def test_messages_persisted_to_db(self, pipeline, adapter, sample_file, master_key, db):
        pipeline.import_conversations(adapter, sample_file, master_key)
        assert db.get_message_count() >= 4  # 2 msgs per conversation

    def test_deduplication_skips_on_reimport(self, pipeline, adapter, sample_file, master_key):
        result1 = pipeline.import_conversations(adapter, sample_file, master_key)
        result2 = pipeline.import_conversations(adapter, sample_file, master_key)
        assert result1.imported == 2
        assert result2.imported == 0
        assert result2.skipped == 2

    def test_blobs_created_for_messages(self, pipeline, adapter, sample_file, master_key, vault_root):
        pipeline.import_conversations(adapter, sample_file, master_key)
        blob_files = list((vault_root / "blobs").rglob("*.enc"))
        assert len(blob_files) >= 4  # at least 2 messages per conversation

    def test_message_content_is_decryptable(
        self, pipeline, adapter, sample_file, master_key, db, blob_store
    ):
        pipeline.import_conversations(adapter, sample_file, master_key)
        convs = db.list_conversations()
        assert convs
        conv = convs[0]
        messages = db.get_messages(conv.id)
        assert messages
        msg = messages[0]
        content = blob_store.retrieve(msg.content_blob_uuid, master_key, conv.id)
        assert len(content) > 0

    def test_progress_callback_called(self, pipeline, adapter, sample_file, master_key):
        calls = []

        def cb(current, total):
            calls.append((current, total))

        pipeline.import_conversations(adapter, sample_file, master_key, progress_callback=cb)
        assert len(calls) > 0

    def test_invalid_file_raises(self, pipeline, adapter, master_key, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json")
        with pytest.raises((ValueError, Exception)):
            pipeline.import_conversations(adapter, bad_file, master_key)

    def test_import_result_total_property(self, pipeline, adapter, sample_file, master_key):
        result = pipeline.import_conversations(adapter, sample_file, master_key)
        assert result.total == result.imported + result.skipped + result.failed
