# Architecture Playbook

High-level design principles and system overview for Project Memento.

## Design Principles
- **Local-first**: All memory data stays on the local machine by default.
- **Encrypt by default**: Content is stored as encrypted blobs; only metadata is plaintext.
- **Composable adapters**: Ingestion is provider-specific, normalised to a shared schema.
- **Minimal metadata**: Store only what is necessary for retrieval and auditability.
- **Fail-closed security**: When in doubt, deny access or encrypt.

## System Overview
- **CLI**: Primary interface for `init`, `import`, `list`, `show`, `stats` (Typer).
- **API**: FastAPI REST server for programmatic access (Phase 5).
- **Ingestion**: Adapter layer — ChatGPT first, then Claude, Perplexity, Ollama.
- **Classification**: Taxonomy engine (Life/Work/Home/System/Ideas), PII detection (Phase 2–3).
- **Storage**: SQLite (WAL) for metadata; encrypted blob store for content; Qdrant for vectors.
- **Security**: Argon2id key derivation, Fernet symmetric encryption, session tokens (30-min expiry).
- **Cache**: Redis for query caching (Phase 5).

## Directory Structure (Target)
```text
/
├── .agent/           # AI agent rules and workflows
├── .github/          # GitHub config, workflows, templates
├── docs/             # Documentation and playbooks
│   ├── intro/        # Project planning and task prompts
│   └── playbooks/    # Operational playbooks
├── vault/            # Python package (source code)
│   ├── cli/          # Typer CLI commands
│   ├── api/          # FastAPI endpoints (Phase 5)
│   ├── config/       # Pydantic configuration models
│   ├── ingestion/    # Provider adapters and import pipeline
│   ├── classification/ # Domain taxonomy and tagging
│   ├── sanitization/ # PII detection and redaction
│   ├── distillation/ # Summarisation and key-point extraction
│   ├── storage/      # SQLAlchemy models, blob store, DB wrapper
│   ├── retrieval/    # Search and query engine
│   └── security/     # Crypto, key management, sessions
├── tests/            # pytest test suites
│   └── fixtures/     # Test data and fixtures
└── config_examples/  # Sample YAML configurations
```

## Data Flow
1. User exports conversations from an LLM provider (e.g., ChatGPT JSON export).
2. CLI invokes import command with the appropriate provider adapter.
3. Adapter parses the export and normalises into `Conversation` / `Message` objects.
4. Import pipeline deduplicates via content hashing (SHA-256).
5. Message content is encrypted with a per-conversation Fernet key (derived via HKDF) and stored as a blob on disk.
6. Metadata (title, timestamps, source, message count) is stored in SQLite.
7. *(Phase 4)* Embeddings are generated and indexed in Qdrant.
8. CLI retrieval commands decrypt and display content on demand, gated by session token.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | SQLite (WAL mode) | Local-first simplicity, no server process, WAL for concurrent reads |
| Encryption | Fernet (AES-128-CBC + HMAC) | High-level API with built-in authentication, part of `cryptography` stdlib |
| Key derivation | Argon2id | Memory-hard KDF resistant to GPU/ASIC brute-force attacks |
| Per-conversation keys | HKDF from master key | Limits blast radius if a single key is compromised |
| Content storage | Blob files on disk | Avoids SQLite blob size limits, enables secure deletion via file overwrite |
| PII detection | Presidio + LLM Guard | Dual approach: pattern-based + NER-based for high recall |
| Vector search | Qdrant | Embeddable, high-performance, supports metadata filtering |
