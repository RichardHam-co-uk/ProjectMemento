# Architecture Playbook

High-level design principles and system overview for ProjectMemento.

ProjectMemento is no longer only an encrypted archive of exported LLM conversations. That foundation remains important, but the target architecture is now a **universal AI memory layer**: a governed, local-first memory bus that cloud agents can write to, local models can read from, and Obsidian can mirror for human visibility.

For the full target-state narrative, see [Universal Memory Layer](../architecture/universal-memory-layer.md).

## Design Principles

- **Local-first**: The authoritative memory store stays on Richard-controlled infrastructure by default.
- **Encrypt by default**: Sensitive content is stored as encrypted blobs; metadata is minimised and policy-controlled.
- **Composable adapters**: Ingestion and export are adapter-driven so ChatGPT, Claude, Codex, Perplexity, Ollama, GitHub, n8n and Obsidian can be added independently.
- **Governed writes**: Non-human writers stage proposed memories first; approval, dedupe and policy checks happen before long-term memory promotion.
- **Human-visible memory**: Approved exportable memory should be mirrored to Obsidian markdown so the system can be inspected, curated and graphed by a human.
- **Model-agnostic retrieval**: LM Studio, Ollama, Open WebUI, Claude Code workers, FlowFinder and other agents consume memory through stable APIs, not direct database coupling.
- **Namespace isolation**: Personal, system, public and client-specific memories must remain separated by namespace and policy.
- **Fail-closed security**: When in doubt, deny access, stage for review, redact, or encrypt.
- **Source-linked and reversible**: Memory records include source attribution, confidence, status and audit metadata so they can be superseded, rejected, expired or deleted.

## System Overview

ProjectMemento has four major layers:

1. **Ingestion and Write Layer**
   - CLI importers for exported conversations.
   - API endpoints for Claude, Codex, ChatGPT, Perplexity, n8n, GitHub and future writer tools.
   - Staging inbox for proposed memories.
   - Policy checks, PII detection, deduplication, source attribution and confidence scoring.

2. **Memory Core**
   - Canonical memory records.
   - Encrypted blob store for source/full content.
   - Metadata database using SQLite initially, with Postgres as a later scalable option.
   - Vector index using Qdrant or pgvector.
   - Optional graph/relationship index for people, projects, clients, systems, repos and decisions.

3. **Retrieval and Context Layer**
   - CLI and FastAPI read operations.
   - Semantic, keyword and metadata-filtered search.
   - Context-pack generation for projects, clients and tasks.
   - Read-only retrieval profiles for local agents and local models.

4. **Human Visibility and Export Layer**
   - One-way Obsidian markdown mirror for approved exportable memories.
   - YAML front matter for Dataview.
   - Obsidian graph links between memories, projects, clients and systems.
   - Later optional Obsidian-to-staging import for notes explicitly marked for ingestion.

## Target Architecture

```text
                    Cloud + Human Writers
  ┌──────────────────────────────────────────────────────┐
  │ Claude / Codex / ChatGPT / Perplexity / n8n / GitHub │
  └──────────────────────────┬───────────────────────────┘
                             │
                             ▼
                  Write API / Import Gateway
       ┌────────────────────────────────────────┐
       │ auth, policy, staging, redaction       │
       │ dedupe, source attribution, approval   │
       └───────────────────┬────────────────────┘
                           │
                           ▼
                  ProjectMemento Memory Core
       ┌────────────────────────────────────────┐
       │ canonical memory records               │
       │ SQLite/Postgres metadata               │
       │ encrypted blob store                   │
       │ Qdrant/pgvector embeddings             │
       │ optional graph relationships           │
       └───────┬──────────────────────┬─────────┘
               │                      │
               ▼                      ▼
       Retrieval API            Obsidian Exporter
 ┌─────────────────────┐   ┌────────────────────────┐
 │ LM Studio / Ollama  │   │ Markdown vault mirror   │
 │ Open WebUI / agents │   │ Dataview properties     │
 │ FlowFinder / tools  │   │ Obsidian graph links    │
 └─────────────────────┘   └────────────────────────┘
```

## Current Foundation Components

- **CLI**: Primary local interface for `init`, `import`, `list`, `show`, `stats` and future `memory` commands.
- **API**: FastAPI REST server for programmatic write/read access.
- **Ingestion**: Adapter layer — ChatGPT first, then Claude, Perplexity, Ollama, Codex/GitHub/n8n patterns.
- **Classification**: Taxonomy engine for domains, memory classes, tags and namespace routing.
- **Sanitisation**: PII detection, redaction and policy checks before approval or export.
- **Storage**: SQLite or Postgres metadata; encrypted blob store; Qdrant or pgvector vector index.
- **Security**: Argon2id key derivation, Fernet symmetric encryption, session tokens, writer profiles and namespace ACLs.
- **Cache**: Redis for session state and query caching where useful.
- **Export**: Obsidian markdown mirror for approved exportable memories.

## Directory Structure (Target)

```text
/
├── .agent/                 # AI agent rules and workflows
├── .github/                # GitHub config, workflows, templates
├── docs/                   # Documentation and playbooks
│   ├── architecture/        # Target-state architecture and design docs
│   ├── intro/               # Project planning and task prompts
│   └── playbooks/           # Operational playbooks
├── vault/                  # Python package (source code)
│   ├── cli/                 # Typer CLI commands
│   ├── api/                 # FastAPI endpoints
│   ├── config/              # Pydantic configuration models
│   ├── ingestion/           # Provider adapters and import pipeline
│   ├── memory/              # Canonical memory schema and lifecycle
│   ├── classification/      # Domain taxonomy, memory typing and tagging
│   ├── sanitization/        # PII detection and redaction
│   ├── distillation/        # Summarisation and key-point extraction
│   ├── storage/             # SQLAlchemy models, blob store, DB wrapper
│   ├── retrieval/           # Search, context packs and query engine
│   ├── export/              # Obsidian and other outbound exporters
│   ├── integrations/        # Claude, Codex, GitHub, n8n, LM Studio, Ollama adapters
│   └── security/            # Crypto, key management, sessions, ACLs
├── tests/                  # pytest test suites
│   └── fixtures/            # Test data and fixtures
└── config_examples/         # Sample YAML configurations
```

## Canonical Memory Record

A memory record should be richer than a raw conversation message.

```yaml
id: mem_...
type: semantic # episodic | semantic | procedural | strategic | project_state | research | relationship
namespace: client/helpdesq
sensitivity: client_confidential # public | internal | client_confidential | restricted
title: Short human-readable title
summary: Distilled memory text
source:
  system: claude # claude | codex | chatgpt | perplexity | n8n | github | obsidian | manual
  uri: github:repo/path-or-session-id
  captured_at: 2026-05-04T00:00:00Z
confidence: 0.86
status: staged # staged | approved | superseded | rejected | expired
retention: review # keep | review | expire | delete_after_date
tags: [helpdesq, kronos, trinity, sql]
links:
  related_memory_ids: []
  related_repos: []
  related_obsidian_notes: []
body: Optional full or expanded content
audit:
  created_by: claude-code
  approved_by: null
  updated_at: 2026-05-04T00:00:00Z
```

## Memory Types

| Type | Purpose | Example |
| --- | --- | --- |
| Episodic | Dated event, meeting, conversation or interaction | "HelpDesQ discovery session identified billing reconciliation pain." |
| Semantic | Durable fact or reusable knowledge | "Ricambio uses Shopify, Sparklayer, Unleashed and PRYSYNK." |
| Procedural | Steps, runbooks or operating patterns | "How to stage a new memory from a Claude Code session." |
| Strategic | Decisions, preferences and long-term direction | "Prefer local-first, human-in-the-loop, client-isolated agent systems." |
| Project state | Current project status, blockers and next actions | "Client-agent-appliance needs generic reusable dashboard docs." |
| Research | Distilled research with sources | "Cloudflare Agent Memory validates memory-as-a-service as an emerging pattern." |
| Relationship | Links between entities | "Lily -> NetSuite -> Boomi -> Azure Fabric migration." |

## Data Flows

### 1. Conversation Import Flow

1. User exports conversations from an LLM provider.
2. CLI invokes import command with the appropriate provider adapter.
3. Adapter parses the export and normalises into conversation/message objects.
4. Import pipeline deduplicates via content hashing.
5. Message content is encrypted and stored in the blob store.
6. Metadata is stored in the metadata database.
7. Optional distillation proposes staged memory records from the imported conversation.
8. Approved memory records are indexed for retrieval.

### 2. Agent Write Flow

```text
Claude/Codex/n8n/GitHub output
  -> Write API
  -> authentication and writer profile
  -> namespace/sensitivity policy check
  -> PII scan and redaction if required
  -> duplicate/similarity check
  -> staged memory record
  -> human approval/edit/reject
  -> approved memory
  -> vector index + retrieval API + optional Obsidian export
```

### 3. Local Agent Retrieval Flow

```text
Local agent asks for task context
  -> Retrieval API with namespace and sensitivity permissions
  -> hybrid search and metadata filtering
  -> approved memories only
  -> compact context pack
  -> local model prompt/RAG/tool context
```

### 4. Obsidian Export Flow

```text
Approved exportable memory
  -> export policy check
  -> markdown render with YAML front matter
  -> folder routing by namespace/type/project
  -> Obsidian graph + Dataview visibility
```

## Obsidian Mirror Design

Obsidian is the human-facing cortex. ProjectMemento remains the canonical machine memory core.

Recommended initial sync direction:

```text
ProjectMemento -> Obsidian markdown mirror
```

Later controlled ingestion:

```text
Obsidian note with memento_ingest: true -> staging inbox -> approval -> canonical memory
```

Obsidian notes must not silently overwrite canonical memory without an explicit staged review process.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Authoritative model | ProjectMemento canonical memory records | Keeps memory governed and auditable rather than scattered across tools |
| Human-readable mirror | Obsidian markdown export | Lets Richard see, curate and graph the AI brain |
| Initial database | SQLite WAL | Local-first simplicity, low operational burden |
| Scalable database option | Postgres | Better for multi-agent/API deployments and client-appliance evolution |
| Vector search | Qdrant or pgvector | Qdrant fits current plan; pgvector simplifies a Postgres-centred appliance |
| Encryption | Fernet/AES with authenticated encryption | High-level safe default for encrypted local blobs |
| Key derivation | Argon2id | Memory-hard KDF resistant to GPU/ASIC brute-force attacks |
| Per-record keys | HKDF from master key | Limits blast radius if a single record key is compromised |
| Content storage | Encrypted blob files | Avoids database blob bloat and supports secure retention/deletion workflows |
| PII detection | Presidio + LLM Guard | Dual approach: pattern-based + NER-based for high recall |
| Write governance | Staging inbox + approval | Prevents AI memory hoarding and untrusted autonomous writes |
| Retrieval policy | Approved records only by default | Stops draft or sensitive content leaking into local model context |
| Client separation | Namespace and sensitivity ACLs | Prevents Lily, HelpDesQ, Ricambio and personal memory cross-contamination |
| Mem0 relationship | Component/reference, not full replacement | Mem0 may help extraction/retrieval, but ProjectMemento remains the governed memory OS |

## Implementation Priorities

1. Keep the secure local vault import path working.
2. Add canonical memory schema and lifecycle state.
3. Add staged memory creation via CLI.
4. Add approval/edit/reject workflow.
5. Add retrieval API for approved memories.
6. Add Obsidian one-way export.
7. Add writer integrations for Claude/Codex/GitHub/n8n.
8. Add context-pack generation for local models and agents.
9. Add namespace/sensitivity policy enforcement.
10. Add monitoring, backup and production deployment profiles.
