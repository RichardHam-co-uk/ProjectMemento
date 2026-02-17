# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — Milestone 1.2-1.3: Core Infrastructure (2026-02-17)
- **KeyManager** (`vault/security/crypto.py`): Argon2id master key derivation, HKDF per-conversation keys, Fernet encryption helpers.
- **BlobStore** (`vault/storage/blobs.py`): Encrypted sharded file storage with atomic writes and secure deletion.
- **SessionManager** (`vault/security/session.py`): Time-limited session tokens with encrypted master key caching.
- Added `argon2-cffi` dependency for Argon2id key derivation.
- Multi-AI task instruction files (`docs/tasks/`) for parallel development across local LLMs, cloud Claude, Gemini, and Perplexity.
- CLAUDE.md project context file for cloud-based Claude sessions.

### Added — Milestone 1.1: Scaffolding (2026-02-17)
- **Pydantic config models** (`vault/config/models.py`): VaultConfig, DatabaseConfig, BlobConfig, VectorConfig, SecurityConfig.
- **SQLAlchemy ORM models** (`vault/storage/models.py`): Conversation, Message, Artifact, PIIFinding, AuditEvent with enums and relationships.
- Minimal Typer CLI entry point (`vault/cli/main.py`) with version command.
- Python package structure under `vault/` with all subpackage scaffolding.
- `pyproject.toml` with Poetry configuration and all Phase 1 dependencies.

### Added — Repository Foundation (2026-02-17)
- Repository scaffolding from best-practice template.
- GitHub workflows for CI and security scanning (CodeQL).
- Development, project management, and architecture playbooks.
- AI agent rules and workflows (`.agent/`).
- GitHub issue templates (bug report, feature request) and PR template.
- CODEOWNERS, CONTRIBUTING, CODE_OF_CONDUCT, and SECURITY policies.
- Phase 1 detailed planning documentation (`docs/intro/`).
