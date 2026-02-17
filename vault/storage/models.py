"""
SQLAlchemy ORM models for the Vault.
"""
import enum
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    JSON,
    Integer,
    Text,
    Boolean,
    Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

# --- Enums ---

class SensitivityLevel(str, enum.Enum):
    """Data sensitivity classification."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class ActorType(str, enum.Enum):
    """Who generated the message/action."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ArtifactType(str, enum.Enum):
    """Type of distilled artifact."""
    SHORT_SUMMARY = "short_summary"
    LONG_SUMMARY = "long_summary"
    KEY_POINTS = "key_points"
    ACTION_ITEMS = "action_items"
    EMBEDDING_TEXT = "embedding_text"

class PIIType(str, enum.Enum):
    """Categories of PII."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    API_KEY = "api_key"
    IP_ADDRESS = "ip_address"
    LOCATION = "location"
    PERSON = "person"
    OTHER = "other"

# --- Models ---

class Conversation(Base):
    """
    Represents a single conversation thread from an LLM provider.
    """
    __tablename__ = "conversations"

    # Primary Key: SHA256 hash of (source + external_id + title + created_at)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    
    # Metadata
    source: Mapped[str] = mapped_column(String, nullable=False, index=True)  # e.g., 'chatgpt', 'claude'
    external_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    
    # Timestamps (UTC)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Classification
    sensitivity: Mapped[SensitivityLevel] = mapped_column(
        SAEnum(SensitivityLevel), 
        default=SensitivityLevel.INTERNAL,
        nullable=False,
        index=True
    )
    domain_tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of tags or taxonomy
    
    # Stats
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Integrity
    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # Content hash for deduplication

    # Relationships
    messages: Mapped[List["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    artifacts: Mapped[List["Artifact"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """
    An individual message within a conversation.
    """
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True) # UUID
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), nullable=False, index=True)
    
    actor: Mapped[ActorType] = mapped_column(SAEnum(ActorType), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Content is stored in Encrypted Blob Storage
    content_blob_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    sanitized_blob_uuid: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    sensitivity: Mapped[SensitivityLevel] = mapped_column(SAEnum(SensitivityLevel), default=SensitivityLevel.INTERNAL)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    pii_findings: Mapped[List["PIIFinding"]] = relationship(back_populates="message", cascade="all, delete-orphan")


class Artifact(Base):
    """
    Derived knowledge distilled from a conversation (summaries, etc).
    """
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True) # UUID
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), nullable=False, index=True)
    
    artifact_type: Mapped[ArtifactType] = mapped_column(SAEnum(ArtifactType), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False) # Often short enough to store in DB (check security policy)
    # Note: If artifacts are sensitive, they should also move to BlobStore. 
    # For v1, we assume summaries of INTERNAL/PUBLIC convos can live in DB if encrypted at volume level.
    # PROPOSAL: Stick to Text for now, move to Blob if content > 4KB or SENSITIVE.
    
    model_used: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    conversation: Mapped["Conversation"] = relationship(back_populates="artifacts")


class PIIFinding(Base):
    """
    Record of PII detected in a message.
    """
    __tablename__ = "pii_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True) # UUID
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"), nullable=False, index=True)
    
    pii_type: Mapped[PIIType] = mapped_column(SAEnum(PIIType), nullable=False)
    span_start: Mapped[int] = mapped_column(Integer, nullable=False)
    span_end: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Integer, nullable=False) # 0.0 to 1.0
    action_taken: Mapped[str] = mapped_column(String, default="redacted") # redacted, masked, removed

    message: Mapped["Message"] = relationship(back_populates="pii_findings")


class AuditEvent(Base):
    """
    Security audit log for all vault access.
    """
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True) # UUID
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    actor: Mapped[str] = mapped_column(String, nullable=False) # Implementation/User ID
    action: Mapped[str] = mapped_column(String, nullable=False) # read, write, delete, search
    resource_type: Mapped[str] = mapped_column(String, nullable=False) # conversation, blob, key
    resource_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)

