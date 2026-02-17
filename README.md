# Project Memento (LLM Memory Vault)

[![Security Scan](https://github.com/zebadee2kk/ProjectMemento/actions/workflows/security-scan.yml/badge.svg)](https://github.com/zebadee2kk/ProjectMemento/actions/workflows/security-scan.yml)
[![CI](https://github.com/zebadee2kk/ProjectMemento/actions/workflows/ci.yml/badge.svg)](https://github.com/zebadee2kk/ProjectMemento/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A local-first, privacy-preserving AI memory system that aggregates conversations from multiple LLM providers (ChatGPT, Claude, Perplexity, Ollama) into a secure, searchable, encrypted personal knowledge base.

**Your conversations. Your machine. Your control.**

## Key Features

- **Encrypted at rest** — AES-256 (Fernet) with Argon2id key derivation; per-conversation keys via HKDF
- **PII detection & redaction** — Presidio + LLM Guard for pattern and NER-based detection
- **Semantic search** — Qdrant vector database with local sentence-transformer embeddings
- **Multi-provider import** — ChatGPT, Claude, Perplexity, Ollama export adapters
- **Classification taxonomy** — 5 domains (Life / Work / Home / System / Ideas) with auto-tagging
- **CLI & REST API** — Typer CLI for daily use, FastAPI server for integrations
- **100% local-first** — your data never leaves your machine

## Tech Stack

Python 3.11+ · Poetry · FastAPI · SQLAlchemy 2.0 · SQLite (WAL) · Qdrant · Redis · Fernet encryption · Argon2id · sentence-transformers · Ollama · Typer CLI · pytest · Black · Ruff · MyPy

## Quick Start

```bash
# Clone and install
git clone https://github.com/zebadee2kk/ProjectMemento.git
cd ProjectMemento
poetry install

# Initialize the vault
poetry run vault init

# Import ChatGPT conversations
poetry run vault import chatgpt <export-file.json>

# Explore your memory
poetry run vault list
poetry run vault show <conversation-id>
poetry run vault stats

# Run tests
poetry run pytest tests/ -v
```

## Architecture Overview

```
CLI (Typer) / API (FastAPI)
        │
   Ingestion Pipeline ← Provider Adapters (ChatGPT, Claude, ...)
        │
   Classification & Sanitization (PII detection, taxonomy tagging)
        │
   Storage Layer
   ├── SQLite (metadata, indexes)
   ├── Encrypted blob store (conversation content)
   └── Qdrant (vector embeddings for semantic search)
        │
   Security Layer (Argon2id KDF, Fernet encryption, session tokens)
```

## AI Readiness

This repo includes AI agent configuration in [.agent/rules.md](.agent/rules.md) and [.agent/workflows/](.agent/workflows/). These guide AI-assisted contributions to follow project conventions.

## Documentation

| Document | Description |
|----------|-------------|
| [Development Playbook](docs/playbooks/development.md) | Setup, coding standards, testing |
| [Architecture Playbook](docs/playbooks/architecture.md) | System design and data flow |
| [Project Management](docs/playbooks/project-management.md) | Issues, PRs, milestones |
| [Security Playbook](docs/playbooks/security.md) | Data security and incident response |
| [Roadmap](ROADMAP.md) | Phase 1–6 delivery plan |
| [Phase 1 Plan](docs/intro/PHASE1_DETAILED_PLAN_1.md) | Detailed Phase 1 tasks and milestones |

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and [docs/playbooks/development.md](docs/playbooks/development.md) for setup instructions.

## Security

For security policy and vulnerability reporting, see [SECURITY.md](SECURITY.md).

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
