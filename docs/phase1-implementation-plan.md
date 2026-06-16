# Phase 1 Implementation Plan — Core Shared Memory Layer

**Issue:** [#7](https://github.com/RichardHam-co-uk/ProjectMemento/issues/7)
**Date:** 2026-06-16
**Author:** Richard Ham ([@RichardHam-co-uk](https://github.com/RichardHam-co-uk))

---

## Overview

ProjectMemento Phase 1 delivers the **core shared memory layer**: a governed, SQLite-backed memory store that agents (Claude, Codex, n8n, etc.) can write to and read from through a Python API. This plan documents the architecture, implementation steps, tech stack, milestones, and success criteria.

> **Note:** Significant Phase 1 work has already been completed on branch `feat/phase1-sqlite-foundation` (commit `33ce2d4`). This plan documents the full Phase 1 scope including both completed and remaining items.

---

## Core Memory Layer Architecture

### Design Principles

1. **Local-first.** All data lives on the local machine. No cloud dependencies for core storage.
2. **Governance-first.** Memories enter as *staged* and must be explicitly *approved* before retrieval by default.
3. **Namespace isolation.** Memories are tagged by namespace (personal, client/*, public) to prevent cross-contamination.
4. **Deterministic identity.** Content hashing ensures idempotent writes — the same content produces the same record.
5. **Agent-friendly API.** A single `MementoAPI` class provides `remember()`, `recall()`, `approve()`, `forget()`.

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      Agents                            │
│  (Claude, Codex, ChatGPT, n8n, Perplexity, manual)    │
└──────────────────────┬──────────────────────────────────┘
                       │ Python API
                       ▼
┌──────────────────────────────────────────────────────────┐
│                   MementoAPI                            │
│  remember()  recall()  approve()  forget()  session()  │
└──────────────────────┬───────────────────────────────────┘
                       │ Pydantic v2 models
                       ▼
┌──────────────────────────────────────────────────────────┐
│                   SQLite Store                           │
│  SQLAlchemy 2.0  │  file-based SQLite  │  CRUD + search │
│  Tables: memories, facts, preferences, sessions          │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│              Encrypted Vault (existing)                  │
│  Argon2id KDF  │  Fernet (AES-128-CBC)  │  blob store  │
└──────────────────────────────────────────────────────────┘
```

### Data Model

| Entity | Purpose | Key Fields |
|--------|---------|------------|
| **Memory** | Canonical memory record (episodic, semantic, procedural, strategic) | `id`, `type`, `namespace`, `title`, `summary`, `body`, `source`, `status`, `content_hash`, `confidence`, `tags`, `created_at`, `updated_at` |
| **Fact** | Atomic factual statement extracted from memories | `id`, `memory_id`, `statement`, `confidence`, `verified`, `content_hash` |
| **Preference** | User/agent preference record | `id`, `namespace`, `key`, `value`, `source`, `content_hash` |
| **Session** | Agent session context for scoped memory access | `id`, `agent`, `namespace`, `token`, `started_at`, `ended_at` |

### Governance Lifecycle

```
┌─────────┐    approve    ┌──────────┐    supersede    ┌────────────┐
│ STAGED  │ ──────────▶   │ APPROVED │ ────────────▶   │ SUPERSEDED │
└─────────┘               └──────────┘                  └────────────┘
     │                        │
     │ reject                 │ expire
     ▼                        ▼
┌─────────┐               ┌────────┐
│REJECTED │               │EXPIRED │
└─────────┘               └────────┘
```

- **Default retrieval mode:** `approved_only=True` — only approved memories are returned by `recall()`.
- **Staged memories** are visible via `recall(status='staged')` for review.
- **Audit trail:** Every state transition is logged with timestamp and actor.

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Language | Python | 3.11+ | Core runtime |
| Data validation | Pydantic | v2.5+ | Model definitions, serialization |
| ORM / Database | SQLAlchemy + SQLite | 2.0+ | Persistent storage |
| Encryption | cryptography (Fernet) | 46.0+ | Encrypted blob storage |
| Key derivation | argon2-cffi | 23.1+ | Password-based key derivation |
| API framework | FastAPI | 0.109+ | HTTP write endpoint (Phase 5) |
| CLI | Typer | 0.9+ | Command-line interface |
| Testing | pytest | 8.0+ | Unit and integration tests |
| Scheduling | systemd timers | — | Periodic consolidation, export |
| Future: Vector search | Qdrant or pgvector | — | Hybrid search (Phase 4) |
| Future: Embeddings | sentence-transformers | — | Local embedding generation (Phase 4) |
| Future: PII detection | Presidio | — | PII scanning (Phase 3) |

---

## Implementation Steps

### Step 1 — Data Models (`src/memento/models.py`) ✅ Complete

- [x] Define `MemoryType` enum: episodic, semantic, procedural, strategic, project_state, research, relationship
- [x] Define `MemoryStatus` enum: staged, approved, superseded, rejected, expired
- [x] Define `MemorySensitivity` enum: public, internal, confidential, restricted
- [x] Define `MemorySource` enum: claude, codex, chatgpt, perplexity, n8n, github, obsidian, manual
- [x] Define `Memory` model with deterministic `content_hash` (SHA-256 of canonical JSON)
- [x] Define `Fact`, `Preference`, `Session` models
- [x] Namespace validation (regex: `^[a-z][a-z0-9_/]{0,63}$`)
- [x] Field validators for all models

### Step 2 — SQLite Store (`src/memento/store.py`) ✅ Complete

- [x] SQLAlchemy 2.0 engine with file-based SQLite
- [x] Table definitions for all entity types
- [x] CRUD operations: `create_memory`, `get_memory`, `update_memory`, `delete_memory`
- [x] Soft delete (status=expired) and hard delete
- [x] Keyword search across title, summary, body, tags
- [x] Governed retrieval: `approved_only` filter by default
- [x] Session lifecycle management
- [x] Fact and Preference CRUD

### Step 3 — Python API (`src/memento/api.py`) ✅ Complete

- [x] `MementoAPI` class with context manager support
- [x] `remember()` — store a new memory (staged by default)
- [x] `recall()` — retrieve memories with filtering
- [x] `approve()` — transition staged → approved
- [x] `forget()` — soft or hard delete
- [x] Session lifecycle: `start_session()`, `end_session()`
- [x] Namespace-scoped operations

### Step 4 — Tests (`tests/`) ✅ Complete

- [x] 36 unit tests covering models, store CRUD, governance workflow, API surface
- [x] All tests passing

### Step 5 — Systemd Timer/Service Definitions (`systemd/`) ✅ Complete

- [x] `memento-staged-report.timer` + `.service` — daily 9am staged memory report
- [x] `memento-consolidation.timer` + `.service` — daily 11pm memory consolidation
- [x] `memento-obsidian-export.timer` + `.service` — daily 10pm Obsidian export

### Step 6 — Session Token Management ⬜ Remaining

- [ ] Implement session token generation (UUID4 or HMAC-based)
- [ ] Token validation in `MementoAPI` for write operations
- [ ] Token expiration and renewal logic
- [ ] CLI command: `memento session create`, `memento session revoke`

### Step 7 — Ingestion Adapters ⬜ Remaining

- [ ] Base `IngestionAdapter` abstract class with `parse()`, `validate()`, `ingest()` methods
- [ ] `ChatGPTJSONAdapter` — parse ChatGPT export JSON format
- [ ] Adapter registry pattern for future adapters (Claude, Perplexity, etc.)

### Step 8 — Import Pipeline with Deduplication ⬜ Remaining

- [ ] Deduplication via content hash comparison before staging
- [ ] Conflict resolution: skip, update, or create-new on hash collision
- [ ] Batch import with progress reporting
- [ ] Import dry-run mode

### Step 9 — CLI Commands ⬜ Remaining

- [ ] `memento import <file>` — import conversation exports
- [ ] `memento list` — list memories with filtering (status, namespace, type)
- [ ] `memento show <id>` — display full memory record
- [ ] `memento stats` — show vault statistics (counts by status, type, namespace)

### Step 10 — Error Handling and Edge Cases ⬜ Remaining

- [ ] Database corruption detection and recovery
- [ ] Graceful handling of malformed input in ingestion adapters
- [ ] Namespace permission enforcement
- [ ] Disk full / quota handling
- [ ] Concurrent access safety (SQLite WAL mode)

---

## Milestones

| Milestone | Target | Status | Deliverable |
|-----------|--------|--------|-------------|
| **M1.1** — Data models & store | Week 1 | ✅ Complete | `models.py`, `store.py` with full CRUD |
| **M1.2** — Python API & tests | Week 2 | ✅ Complete | `api.py`, 36 passing tests |
| **M1.3** — Systemd timers | Week 2 | ✅ Complete | 3 timer+service pairs |
| **M1.4** — Session tokens | Week 3 | ⬜ Pending | Token management CLI |
| **M1.5** — Ingestion adapters | Week 3–4 | ⬜ Pending | Base adapter + ChatGPT adapter |
| **M1.6** — Import pipeline | Week 4 | ⬜ Pending | `memento import` with dedup |
| **M1.7** — CLI & error handling | Week 5 | ⬜ Pending | Full CLI, edge case coverage |

---

## Success Criteria

Phase 1 is considered complete when:

1. **Core API works:** An agent can call `remember()` to stage a memory and `recall()` to retrieve approved memories.
2. **Governance enforced:** Staged memories are not returned by default `recall()`. Explicit `approve()` required.
3. **Data persists:** All data survives process restart (SQLite on disk).
4. **Tests pass:** All unit tests pass with `pytest`.
5. **CLI functional:** `memento import`, `list`, `show`, `stats` commands work.
6. **ChatGPT import works:** A ChatGPT JSON export can be imported into the vault.
7. **Session management:** Agents can create and use scoped sessions.
8. **Error handling:** Malformed input, missing data, and edge cases are handled gracefully.
9. **Activation tier:** timer/service (score ~18) — systemd units call explicit CLI commands, log locally, do not auto-approve memories.

---

## Remaining Work Estimate

| Item | Complexity | Est. Effort |
|------|-----------|-------------|
| Session token management | Medium | 1–2 days |
| Base ingestion adapter + ChatGPT adapter | Medium | 2–3 days |
| Import pipeline with deduplication | Medium | 2–3 days |
| CLI commands (import, list, show, stats) | Low–Medium | 1–2 days |
| Error handling and edge cases | Medium | 2–3 days |
| **Total remaining** | | **8–13 days** |

---

## References

- **ROADMAP:** [`ROADMAP.md`](../../ROADMAP.md) — Phase 1 checklist items
- **SSOT:** <https://github.com/zebadee2kk/hermes-mgmt/blob/main/docs/agent-recon-portfolio.md>
- **Activation scoring:** <https://github.com/zebadee2kk/hermes-mgmt/blob/main/docs/activation-scoring-schema.md>
- **Completed implementation:** Branch `feat/phase1-sqlite-foundation`, commit `33ce2d4`
