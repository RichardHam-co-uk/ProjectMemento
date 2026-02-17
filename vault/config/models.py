"""
Configuration models using Pydantic.
"""
from pathlib import Path
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, SecretStr
from enum import Enum

class DatabaseConfig(BaseModel):
    """Configuration for SQLite storage."""
    db_path: Path = Field(
        default=Path("vault_data/vault.db"),
        description="Path to the SQLite database file"
    )
    echo_sql: bool = Field(default=False, description="Log SQL queries")

class BlobConfig(BaseModel):
    """Configuration for encrypted blob storage."""
    storage_path: Path = Field(
        default=Path("vault_data/blobs"),
        description="Root directory for encrypted blobs"
    )
    encryption_algorithm: str = Field(default="Fernet", description="Encryption algorithm")

class VectorConfig(BaseModel):
    """Configuration for Vector Database (Qdrant)."""
    host: str = Field(default="localhost", description="Qdrant host")
    port: int = Field(default=6333, description="Qdrant port")
    collection_name: str = Field(default="conversations", description="Collection name")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace model for embeddings"
    )

class SecurityConfig(BaseModel):
    """Security and Data Privacy policies."""
    min_passphrase_length: int = Field(default=12, description="Minimum passphrase length")
    session_timeout_minutes: int = Field(default=30, description="Session expiry time")
    pii_detection_enabled: bool = Field(default=True, description="Enable PII scanning")

class VaultConfig(BaseModel):
    """Main application configuration."""
    vault_root: Path = Field(
        default=Path("vault_data"),
        description="Root directory for vault storage"
    )
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    blobs: BlobConfig = Field(default_factory=BlobConfig)
    vectors: VectorConfig = Field(default_factory=VectorConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    class Config:
        env_prefix = "VAULT_"
