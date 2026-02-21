# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — Phase 1: Foundation & ChatGPT Import (complete as of 2026-02-21)

#### Security & Encryption
- `vault/security/crypto.py` — `KeyManager`: Argon2id (t=4, m=64 MB, p=4) master-key derivation, HKDF-SHA256 per-conversation keys, Fernet encrypt/decrypt, in-memory key cache, salt persistence.
- `vault/security/session.py` — `SessionManager`: 30-minute session tokens, master key encrypted on disk, constant-time token comparison, 0600 file permissions.

#### Storage
- `vault/storage/models.py` — SQLAlchemy 2.x ORM models: `Conversation`, `Message`, `Artifact`, `PIIFinding`, `AuditEvent`; enums `SensitivityLevel`, `ActorType`, `ArtifactType`, `PIIType`.
- `vault/storage/migrations.py` — Lightweight migration registry (not Alembic); `get_current_version`, `apply_migrations`, `needs_migration`; v1 initial schema.
- `vault/storage/blobs.py` — `BlobStore`: sharded encrypted blob storage, atomic writes, secure deletion (overwrite + unlink), 0600 permissions.
- `vault/storage/db.py` — `VaultDB`: SQLAlchemy engine with WAL/FK/synchronous pragmas, transactional session context manager, 9 query methods including `get_conversation_by_prefix` for prefix-based lookup.

#### Configuration
- `vault/config/models.py` — Pydantic v2 config models: `VaultConfig`, `DatabaseConfig`, `BlobConfig`, `SecurityConfig`, `VectorConfig`; `VAULT_` env-var overrides.

#### Ingestion
- `vault/ingestion/base.py` — `BaseAdapter` Protocol, `ParsedMessage` / `ParsedConversation` / `ImportResult` dataclasses, utility functions `normalize_timestamp`, `generate_conversation_hash`, `deduplicate_messages`.
- `vault/ingestion/chatgpt.py` — `ChatGPTAdapter`: parses ChatGPT JSON exports (tree/mapping format → linear message list), 100 MB size limit, metadata extraction.
- `vault/ingestion/pipeline.py` — `ImportPipeline`: deduplication via SHA-256 content hashes, atomic per-conversation transactions, progress callback.

#### CLI (`vault/cli/main.py`)
- `vault version` — prints CLI version.
- `vault init` — passphrase prompt (min 12 chars + confirm), Argon2id key derivation, schema initialisation, session token creation.
- `vault import <provider> <file>` — delegates to registered adapter, Rich progress bar, import summary table.
- `vault list` — paginated conversation table (ID prefix, source, title, message count, date); `--limit`, `--source` filters.
- `vault show <id>` — decrypts and displays conversation messages; accepts full ID or unique prefix; `--metadata` for header-only view; `--limit` to cap messages shown.
- `vault stats` — Rich panel: total conversations/messages, date range, per-source breakdown.
- `vault lock` — clears active session file.
- Session management via `VAULT_SESSION_TOKEN` environment variable (`_authenticate` helper).

#### Developer tooling
- `pyproject.toml` — all core and dev dependencies, CLI entry point, black/ruff/mypy/pytest configuration.
- `.pre-commit-config.yaml` — black, ruff, mypy, bandit, detect-private-key.
- `tests/` — scaffolded test files for all modules with `conftest.py` fixtures (`tmp_vault_path`, `sample_passphrase`, `weak_passphrase`).

### Added — Project Scaffolding (2026-02-17)
- Repository scaffolding from best-practice template.
- GitHub workflows for CI and security scanning (CodeQL).
- Development, project management, and architecture playbooks.
- AI agent rules and workflows (`.agent/`).
- GitHub issue templates (bug report, feature request) and PR template.
- CODEOWNERS, CONTRIBUTING, CODE_OF_CONDUCT, and SECURITY policies.
- Phase 1 detailed planning documentation (`docs/intro/`).
- ROADMAP.md covering Phases 1–6.
- SECURITY.md with Zero Trust policies.
