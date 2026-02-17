# Project Memento — Claude Context File

This file provides context for any Claude session (local or cloud) working on this project.

## Project Summary

**LLM Memory Vault** — A local-first, privacy-preserving AI memory system that aggregates conversations from multiple LLM providers (ChatGPT, Claude, Perplexity, Ollama) into a secure, searchable, encrypted personal knowledge base.

**Tech stack:** Python 3.13 · Poetry · FastAPI · SQLAlchemy 2.0 · SQLite (WAL) · Qdrant · Fernet encryption · Argon2id · Typer CLI · Rich

## Current Status (Updated: 2026-02-17, Session 3)

### Completed
- **Milestone 1.1 (Scaffolding):** Full Python package structure, Pydantic config, ORM models, minimal CLI
- **Milestone 1.2-1.3 (Core Security):** KeyManager (crypto.py), BlobStore (blobs.py), SessionManager (session.py) — all smoke tested
- **Opus Review:** Task assignments verified, Gantt chart created, build order confirmed (see `docs/OPUS_REVIEW_2026-02-17.md`)

### In Progress — Phase 1: Foundation & ChatGPT Import
See `docs/tasks/` for detailed task files with prompts and acceptance criteria.

### What Still Needs Building
| Task | File | Status | Assigned To | Branch |
|------|------|--------|-------------|--------|
| 1.2.2 Migration system | `vault/storage/migrations.py` | Not started | Local LLM (Qwen/DeepSeek) | ai/feat-local-scaffolding |
| 1.4.1 Database wrapper | `vault/storage/db.py` | Not started | Sonnet/Gemini | ai/feat-cloud-tasks |
| 1.6.1 Base adapter interface | `vault/ingestion/base.py` | Not started | Local LLM (Qwen/DeepSeek) | ai/feat-local-scaffolding |
| 1.6.2 ChatGPT adapter | `vault/ingestion/chatgpt.py` | Not started | Claude Code (Sonnet) | ai/feat-core-infrastructure |
| 1.4.2 vault init CLI | `vault/cli/main.py` | Not started | Claude Code (Sonnet) | ai/feat-core-infrastructure |
| 1.5.2 Session CLI integration | `vault/cli/main.py` | Not started | Claude Haiku | ai/feat-cloud-tasks |
| 1.8.1 Import pipeline | `vault/ingestion/pipeline.py` | Not started | Claude Code (Sonnet) | ai/feat-core-infrastructure |
| 1.8.2 vault import CLI | `vault/cli/main.py` | Not started | Claude Haiku | ai/feat-cloud-tasks |
| 1.9.1 vault list command | `vault/cli/main.py` | Not started | Local LLM/Copilot | ai/feat-local-scaffolding |
| 1.9.2 vault show command | `vault/cli/main.py` | Not started | Claude Haiku | ai/feat-cloud-tasks |
| 1.9.3 vault stats command | `vault/cli/main.py` | Not started | Local LLM/Copilot | ai/feat-local-scaffolding |
| 1.9.4 Error handling polish | `vault/cli/main.py` | Not started | Claude Haiku | ai/feat-cloud-tasks |
| Unit tests | `tests/test_*.py` | Not started | Claude Haiku | ai/feat-cloud-tasks |
| Integration tests | `tests/test_integration.py` | Not started | Claude Code (Sonnet) | ai/feat-core-infrastructure |
| Security review | (review only) | Partial (assignment review done) | Claude Opus | — |
| Test scaffolding | `tests/` | Not started | Local LLM (Llama3b) | ai/feat-local-scaffolding |
| Research x3 | `docs/tasks/RESEARCH-RESULTS.md` | Not started | Perplexity | — |

### Cloud Claude Quick-Start Tasks (no dependencies)
If you're cloud Claude on mobile, start here:
1. **Unit tests for crypto.py** — Read `vault/security/crypto.py`, write `tests/test_crypto.py`
2. **Unit tests for blobs.py** — Read `vault/storage/blobs.py`, write `tests/test_blobs.py`
3. **Unit tests for session.py** — Read `vault/security/session.py`, write `tests/test_session.py`

These require no other modules to exist. Use Haiku. Commit to `ai/feat-cloud-tasks`.

## Branching Strategy

Each agent/platform works on its own branch:
- `ai/feat-core-infrastructure` — Claude Code (local VSCode session)
- `ai/feat-local-scaffolding` — Local LLMs via Continue extension
- `ai/feat-cloud-tasks` — Cloud Claude (mobile sessions)

All branches merge to `main` via Pull Request with squash merge.

## Key Architecture Decisions

- **Encryption:** Fernet (AES-128-CBC + HMAC) with per-conversation keys derived via HKDF from Argon2id master key
- **Storage:** Encrypted blob files on disk (sharded by first 2 chars of UUID), metadata in SQLite
- **Sessions:** Random token in memory, SHA-256 hash + encrypted master key on disk, 30-min expiry
- **No plaintext on disk ever** — all conversation content encrypted before write

## Conventions

- **Docstrings:** Google style
- **Type hints:** Required on all public functions
- **Naming:** snake_case (functions), PascalCase (classes), UPPER_CASE (constants)
- **Commits:** Conventional Commits (feat:, fix:, docs:, chore:, test:)
- **Testing:** pytest, >80% coverage target
- **Formatting:** black, ruff, mypy

## Key Files

| File | Purpose |
|------|---------|
| `vault/config/models.py` | Pydantic configuration models |
| `vault/storage/models.py` | SQLAlchemy ORM (Conversation, Message, etc.) |
| `vault/security/crypto.py` | KeyManager — Argon2id + HKDF + Fernet |
| `vault/storage/blobs.py` | BlobStore — encrypted file storage |
| `vault/security/session.py` | SessionManager — token-based auth |
| `vault/cli/main.py` | Typer CLI entry point |
| `docs/intro/PHASE1_DETAILED_PLAN_1.md` | Master plan with all task specifications |
| `docs/tasks/*.md` | Individual task instruction files |
| `ROADMAP.md` | Phase 1-6 delivery plan |

## Rules for AI Agents

1. **Work on your assigned branch** — never commit directly to main
2. **Read existing code before modifying** — understand patterns first
3. **Only work on tasks assigned to your tier** — leave other tasks alone
4. **Run quality checks:** `poetry run pytest`, `poetry run ruff check .`, `poetry run black --check .`
5. **Follow Conventional Commits** for all commit messages
6. **Never log or expose keys, passphrases, or decrypted content**
7. **Update CHANGELOG.md** when completing a milestone
