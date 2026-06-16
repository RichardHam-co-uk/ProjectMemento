"""File-backed deterministic memory store.

This is deliberately small: a JSONL append/replace file gives Phase 1 a local,
auditable storage backend without introducing the full daemon/API/vector stack.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from vault.memory.models import MemoryRecord, MemoryStatus, StagedMemoryRequest


@dataclass(frozen=True)
class MemoryFilters:
    status: MemoryStatus | None = None
    namespace: str | None = None
    memory_type: str | None = None
    sensitivity: str | None = None
    query: str | None = None


class DuplicateMemoryError(ValueError):
    """Raised when deterministic content already exists in the store."""


class MemoryNotFoundError(KeyError):
    """Raised when a requested memory id is absent."""


class FileMemoryStore:
    """A deterministic JSONL memory store.

    Records are sorted by id on every write, so the backing file is stable
    across repeated runs and easy to diff in early development.
    """

    def __init__(self, root: Path | str = "vault_data") -> None:
        self.root = Path(root)
        self.path = self.root / "memory" / "memories.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def init(self) -> Path:
        """Create the memory store if it does not already exist."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_records([])
        return self.path

    def stage(self, request: StagedMemoryRequest) -> MemoryRecord:
        """Create a staged memory, rejecting exact duplicates."""
        records = self.list()
        record = MemoryRecord.from_request(request)
        if any(existing.id == record.id for existing in records):
            raise DuplicateMemoryError(f"memory already exists: {record.id}")
        records.append(record)
        self._write_records(records)
        return record

    def get(self, memory_id: str) -> MemoryRecord:
        for record in self.list():
            if record.id == memory_id:
                return record
        raise MemoryNotFoundError(memory_id)

    def list(self, filters: MemoryFilters | None = None) -> list[MemoryRecord]:
        self.init()
        records: list[MemoryRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            records.append(MemoryRecord.model_validate_json(line))
        records.sort(key=lambda item: item.id)
        if filters is None:
            return records
        return [record for record in records if self._matches(record, filters)]

    def approve(self, memory_id: str, approved_by: str = "local") -> MemoryRecord:
        return self._transition(
            memory_id,
            MemoryStatus.APPROVED,
            reason=None,
            approved_by=approved_by,
        )

    def reject(self, memory_id: str, reason: str) -> MemoryRecord:
        return self._transition(memory_id, MemoryStatus.REJECTED, reason=reason)

    def search(
        self,
        query: str,
        *,
        namespace: str | None = None,
        include_staged: bool = False,
    ) -> list[MemoryRecord]:
        """Keyword search over summaries/titles/tags.

        Retrieval is governed: approved records only unless include_staged=True.
        """
        status = None if include_staged else MemoryStatus.APPROVED
        return self.list(MemoryFilters(status=status, namespace=namespace, query=query))

    def _transition(
        self,
        memory_id: str,
        status: MemoryStatus,
        *,
        reason: str | None = None,
        approved_by: str | None = None,
    ) -> MemoryRecord:
        records = self.list()
        updated: MemoryRecord | None = None
        for index, record in enumerate(records):
            if record.id != memory_id:
                continue
            data = record.model_dump()
            data.update(
                {
                    "status": status,
                    "status_reason": reason,
                    "approved_by": approved_by or record.approved_by,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            updated = MemoryRecord.model_validate(data)
            records[index] = updated
            break
        if updated is None:
            raise MemoryNotFoundError(memory_id)
        self._write_records(records)
        return updated

    def _write_records(self, records: list[MemoryRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        sorted_records = sorted(records, key=lambda item: item.id)
        content = "".join(
            json.dumps(record.model_dump(mode="json"), sort_keys=True) + "\n"
            for record in sorted_records
        )
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, self.path)

    @staticmethod
    def _matches(record: MemoryRecord, filters: MemoryFilters) -> bool:
        if filters.status is not None and record.status != filters.status:
            return False
        if filters.namespace and record.namespace != filters.namespace:
            return False
        if filters.memory_type and record.type.value != filters.memory_type:
            return False
        if filters.sensitivity and record.sensitivity.value != filters.sensitivity:
            return False
        if filters.query:
            haystack = " ".join(
                [
                    record.title,
                    record.summary,
                    " ".join(record.tags),
                    record.body or "",
                ]
            ).lower()
            needles = [part for part in filters.query.lower().split() if part]
            return all(needle in haystack for needle in needles)
        return True
