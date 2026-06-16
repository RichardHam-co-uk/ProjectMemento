from pathlib import Path

import pytest
from pydantic import ValidationError

from vault.memory.models import MemorySensitivity, MemoryStatus, MemoryType, StagedMemoryRequest
from vault.memory.store import DuplicateMemoryError, FileMemoryStore


def request(**overrides) -> StagedMemoryRequest:
    payload = {
        "type": "project_state",
        "namespace": "project/projectmemento",
        "sensitivity": "internal",
        "title": "Phase 1 foundation started",
        "summary": "ProjectMemento has a deterministic local memory layer.",
        "source": {"system": "codex", "uri": "ProjectMemento#7"},
        "confidence": 0.8,
        "tags": ["phase-1", "Memory", "phase-1"],
        "body": "Implementation notes that should be hidden by default.",
        "created_by": "test-agent",
    }
    payload.update(overrides)
    return StagedMemoryRequest.model_validate(payload)


def test_request_defaults_sensitivity_to_restricted() -> None:
    staged = request(sensitivity="restricted")
    payload = staged.model_dump()
    payload.pop("sensitivity")

    parsed = StagedMemoryRequest.model_validate(payload)

    assert parsed.sensitivity == MemorySensitivity.RESTRICTED


def test_invalid_enum_and_namespace_rejected() -> None:
    with pytest.raises(ValidationError):
        request(type="unknown")

    with pytest.raises(ValidationError):
        request(namespace="random/team")


def test_client_namespace_fails_closed_for_low_sensitivity() -> None:
    with pytest.raises(ValidationError):
        request(namespace="client/helpdesq", sensitivity="internal")

    parsed = request(namespace="client/helpdesq", sensitivity="client_confidential")
    assert parsed.namespace == "client/helpdesq"


def test_stage_is_deterministic_and_duplicate_safe(tmp_path: Path) -> None:
    store = FileMemoryStore(tmp_path)
    first = store.stage(request())

    assert first.id == request().deterministic_id()
    assert first.status == MemoryStatus.STAGED
    assert first.type == MemoryType.PROJECT_STATE

    with pytest.raises(DuplicateMemoryError):
        store.stage(request())


def test_search_returns_approved_only_by_default(tmp_path: Path) -> None:
    store = FileMemoryStore(tmp_path)
    staged = store.stage(request(summary="alpha beta gamma"))

    assert store.search("alpha") == []

    approved = store.approve(staged.id, approved_by="richard")

    assert approved.status == MemoryStatus.APPROVED
    assert [record.id for record in store.search("alpha beta")] == [staged.id]
    assert store.search("alpha", namespace="project/other") == []


def test_safe_view_hides_body_by_default(tmp_path: Path) -> None:
    store = FileMemoryStore(tmp_path)
    staged = store.stage(request())

    safe = store.get(staged.id).safe_view()
    full = store.get(staged.id).safe_view(include_body=True)

    assert safe["body"].startswith("[hidden")
    assert full["body"] == "Implementation notes that should be hidden by default."
