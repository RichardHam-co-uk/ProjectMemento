"""Canonical memory models for the minimal deterministic memory layer.

Phase 1 intentionally keeps these models small and dependency-light while
matching the target universal memory shape documented in the roadmap.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class MemoryType(str, Enum):
    """Supported canonical memory classes."""

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    STRATEGIC = "strategic"
    PROJECT_STATE = "project_state"
    RESEARCH = "research"
    RELATIONSHIP = "relationship"


class MemoryStatus(str, Enum):
    """Governance lifecycle states."""

    STAGED = "staged"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    EXPIRED = "expired"


class MemorySensitivity(str, Enum):
    """Fail-closed sensitivity classes."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CLIENT_CONFIDENTIAL = "client_confidential"
    RESTRICTED = "restricted"


ALLOWED_ROOT_NAMESPACES = {"personal", "public", "system", "project", "client"}


class MemorySource(BaseModel):
    """Source attribution for a memory proposal."""

    system: str = Field(..., min_length=1)
    uri: str | None = None
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StagedMemoryRequest(BaseModel):
    """Input contract for human or agent generated memory proposals."""

    type: MemoryType
    namespace: str = Field(..., min_length=1)
    sensitivity: MemorySensitivity = MemorySensitivity.RESTRICTED
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1)
    source: MemorySource
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    retention: str = "review"
    tags: list[str] = Field(default_factory=list)
    links: dict[str, list[str]] = Field(default_factory=dict)
    body: str | None = None
    created_by: str = "unknown"

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, value: str) -> str:
        value = value.strip().strip("/").lower()
        if not value:
            raise ValueError("namespace must not be empty")
        root = value.split("/", 1)[0]
        if root not in ALLOWED_ROOT_NAMESPACES:
            raise ValueError(
                "namespace must start with one of: "
                + ", ".join(sorted(ALLOWED_ROOT_NAMESPACES))
            )
        return value

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        return sorted({tag.strip().lower() for tag in values if tag.strip()})

    @model_validator(mode="after")
    def client_namespace_requires_client_confidential_or_restricted(
        self,
    ) -> "StagedMemoryRequest":
        if self.namespace.startswith("client/") and self.sensitivity in {
            MemorySensitivity.PUBLIC,
            MemorySensitivity.INTERNAL,
        }:
            raise ValueError(
                "client namespaces must use client_confidential or restricted sensitivity"
            )
        return self

    def deterministic_payload(self) -> dict[str, Any]:
        """Return the stable fields used for content hashing and ID generation."""
        return {
            "type": self.type.value,
            "namespace": self.namespace,
            "sensitivity": self.sensitivity.value,
            "title": self.title.strip(),
            "summary": self.summary.strip(),
            "source": {
                "system": self.source.system.strip().lower(),
                "uri": self.source.uri,
            },
            "retention": self.retention,
            "tags": self.tags,
            "links": self.links,
            "body": self.body,
        }

    def compute_content_hash(self) -> str:
        return _sha256_json(self.deterministic_payload())

    def deterministic_id(self) -> str:
        return f"mem_{self.compute_content_hash()[:16]}"


class MemoryRecord(StagedMemoryRequest):
    """Stored memory record.

    Body is retained in the local JSONL backend for Phase 1 only. Later phases
    can replace this with encrypted blob pointers without changing the CLI
    contract or deterministic metadata behaviour.
    """

    id: str
    status: MemoryStatus = MemoryStatus.STAGED
    content_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status_reason: str | None = None
    approved_by: str | None = None

    @classmethod
    def from_request(cls, request: StagedMemoryRequest) -> "MemoryRecord":
        now = datetime.now(timezone.utc)
        return cls(
            **request.model_dump(),
            id=request.deterministic_id(),
            status=MemoryStatus.STAGED,
            content_hash=request.compute_content_hash(),
            created_at=now,
            updated_at=now,
        )

    def safe_view(self, include_body: bool = False) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        if not include_body and data.get("body"):
            data["body"] = "[hidden; use --include-body for local inspection]"
        return data


def _sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
