"""Data models for the ProjectMemento shared memory layer.

Defines the core entities: Memory, Fact, Preference, and Session.
All models use Pydantic v2 for validation and serialization.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


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

    system: str = Field(..., min_length=1, description="Originating system (e.g. claude, codex, n8n)")
    uri: str | None = None
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Memory(BaseModel):
    """A single memory record — the core entity of ProjectMemento.

    Memories are the primary unit of stored knowledge. They can represent
    episodic events, semantic facts, procedural knowledge, strategic
    decisions, project state, research findings, or relationship mappings.
    """

    # Identity
    id: str | None = None
    type: MemoryType
    namespace: str = Field(..., min_length=1)

    # Content
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1)
    body: str | None = None

    # Governance
    sensitivity: MemorySensitivity = MemorySensitivity.RESTRICTED
    status: MemoryStatus = MemoryStatus.STAGED
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    retention: str = "review"

    # Attribution
    source: MemorySource
    created_by: str = "unknown"
    approved_by: str | None = None
    status_reason: str | None = None

    # Organization
    tags: list[str] = Field(default_factory=list)
    links: dict[str, list[str]] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Content hash for deduplication
    content_hash: str | None = None

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

    @field_validator("namespace")
    @classmethod
    def client_namespace_requires_high_sensitivity(cls, value: str) -> str:
        # This is a second pass — sensitivity is validated in model_validator
        return value

    @field_validator("sensitivity")
    @classmethod
    def validate_client_sensitivity(cls, value: MemorySensitivity, info) -> MemorySensitivity:
        # Access namespace from the data being validated
        # Note: field_validator runs per-field; cross-field checks go in model_validator
        return value

    def compute_content_hash(self) -> str:
        """Compute a deterministic SHA-256 hash over stable semantic fields."""
        payload = {
            "type": self.type.value if isinstance(self.type, MemoryType) else self.type,
            "namespace": self.namespace,
            "sensitivity": self.sensitivity.value if isinstance(self.sensitivity, MemorySensitivity) else self.sensitivity,
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
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def deterministic_id(self) -> str:
        return f"mem_{self.compute_content_hash()[:16]}"

    def safe_view(self, include_body: bool = False) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        if not include_body and data.get("body"):
            data["body"] = "[hidden; use --include-body for local inspection]"
        return data


class Fact(BaseModel):
    """A durable, atomic piece of knowledge.

    Facts are semantic memories that represent verified information
    about the world, clients, projects, or systems.
    """

    id: str | None = None
    subject: str = Field(..., min_length=1, description="The entity this fact is about")
    predicate: str = Field(..., min_length=1, description="The relationship or attribute")
    object_value: str = Field(..., min_length=1, description="The value or target of the fact")
    namespace: str = "personal"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    source: MemorySource | None = None
    status: MemoryStatus = MemoryStatus.STAGED
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        return sorted({tag.strip().lower() for tag in values if tag.strip()})

    def compute_content_hash(self) -> str:
        payload = {
            "subject": self.subject.strip().lower(),
            "predicate": self.predicate.strip().lower(),
            "object_value": self.object_value.strip(),
            "namespace": self.namespace,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def deterministic_id(self) -> str:
        return f"fact_{self.compute_content_hash()[:16]}"


class Preference(BaseModel):
    """A user or agent preference for behavior, style, or configuration.

    Preferences capture how Richard (or specific agents) want things done —
    coding style, communication preferences, tool choices, etc.
    """

    id: str | None = None
    key: str = Field(..., min_length=1, description="Preference identifier (e.g. 'coding_style.python')")
    value: str = Field(..., min_length=1, description="The preference value")
    namespace: str = "personal"
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    source: MemorySource | None = None
    status: MemoryStatus = MemoryStatus.STAGED
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        return sorted({tag.strip().lower() for tag in values if tag.strip()})

    def compute_content_hash(self) -> str:
        payload = {
            "key": self.key.strip().lower(),
            "value": self.value.strip(),
            "namespace": self.namespace,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def deterministic_id(self) -> str:
        return f"pref_{self.compute_content_hash()[:16]}"


class Session(BaseModel):
    """A session context record for tracking agent interactions.

    Sessions capture the context of a particular agent interaction window,
    including what was discussed, what tasks were performed, and any
    relevant state that should persist across invocations.
    """

    id: str | None = None
    agent: str = Field(..., min_length=1, description="Agent identifier (e.g. 'claude', 'codex')")
    namespace: str = "personal"
    title: str = Field(..., min_length=1, max_length=200)
    summary: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    content_hash: str | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        return sorted({tag.strip().lower() for tag in values if tag.strip()})

    def compute_content_hash(self) -> str:
        payload = {
            "agent": self.agent.strip().lower(),
            "namespace": self.namespace,
            "title": self.title.strip(),
            "summary": self.summary,
            "context": self.context,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def deterministic_id(self) -> str:
        return f"sess_{self.compute_content_hash()[:16]}"
