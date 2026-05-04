# Project Memento (Universal AI Memory Layer)

[![Security Scan](https://github.com/zebadee2kk/ProjectMemento/actions/workflows/security-scan.yml/badge.svg)](https://github.com/zebadee2kk/ProjectMemento/actions/workflows/security-scan.yml)
[![CI](https://github.com/zebadee2kk/ProjectMemento/actions/workflows/ci.yml/badge.svg)](https://github.com/zebadee2kk/ProjectMemento/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ProjectMemento is a local-first, privacy-preserving **universal memory layer** for human + multi-agent collaboration.

It is designed to let cloud tools and coding agents such as Claude, Codex, ChatGPT, Perplexity and n8n **write** durable knowledge into a governed memory store, while local models and local agents such as LM Studio, Ollama, Open WebUI, FlowFinder and Claude Code workers can **read** from that same memory so they share context rather than each living in a separate silo.

ProjectMemento also mirrors approved memories into Obsidian so the long-term AI memory is not hidden inside a database: Richard can see, browse, edit, link and graph the full "brain" of memories.

**Your conversations. Your projects. Your agents. Your memory. Your control.**

## What ProjectMemento Should Become

ProjectMemento started as an encrypted local LLM conversation vault. It now becomes the shared memory substrate for Richard's wider WorkOS, local AI stack, GitHub project estate, client-agent-appliance work, and personal knowledge system.

The north star is simple:

> Claude, Codex and other cloud agents can write to it. Local models and agents can read from it. Obsidian makes it visible. Governance keeps it safe.

## Key Features

- **Universal memory bus** — shared memory layer for Claude, Codex, ChatGPT, Perplexity, n8n, local agents and local models
- **Local-first authoritative store** — memory remains on Richard-controlled infrastructure by default
- **Governed write pipeline** — staged writes, approval, confidence scoring, deduplication and source attribution
- **Local model retrieval** — LM Studio, Ollama, Open WebUI and agent runtimes can retrieve approved context through API/RAG interfaces
- **Obsidian visible brain** — approved memories can be mirrored to markdown with front matter, links, tags and graph visibility
- **Encrypted at rest** — AES/Fernet encryption with Argon2id key derivation and per-conversation/per-record key strategy
- **PII detection & redaction** — Presidio + LLM Guard for pattern and NER-based detection
- **Semantic search** — Qdrant or pgvector-backed vector search with local embeddings
- **Multi-provider import** — ChatGPT, Claude, Perplexity, Ollama and future adapters
- **Classification taxonomy** — personal, work, client, system, idea, project, procedural and strategic memory classes
- **CLI & REST API** — Typer CLI for daily use, FastAPI server for integrations
- **Client namespace isolation** — Lily's Kitchen, HelpDesQ, Ricambio and future clients remain separated by policy

## Target Use Cases

- Build a durable personal/company memory layer across ChatGPT, Claude, Codex and local models
- Let Claude Code and Codex write project summaries, decisions and repo state back into memory
- Let local LM Studio/Ollama agents retrieve approved memory so they "know" the relevant context
- Automatically export approved memories into Obsidian for visual review, graphing and human curation
- Generate context packs for projects such as FlowFinder, Client-Agent-Appliance, Local AI Assistant MVP and Claude Local Agents
- Maintain client-specific memory namespaces for Lily's Kitchen, HelpDesQ, Ricambio and future consulting pilots
- Preserve security, privacy, auditability, retention and human-in-the-loop approval for sensitive memories

## Tech Stack

Python 3.11+ · Poetry · FastAPI · Typer CLI · SQLAlchemy 2.0 · SQLite/Postgres · Qdrant or pgvector · Redis · Fernet encryption · Argon2id · sentence-transformers · Ollama/LM Studio integration · Obsidian markdown export · pytest · Black · Ruff · MyPy

## Quick Start

```bash
# Clone and install
git clone https://github.com/RichardHam-co-uk/ProjectMemento.git
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

# Future universal memory operations
poetry run vault memory stage <memory-file.yaml>
poetry run vault memory approve <memory-id>
poetry run vault memory search "client agent appliance dashboard"
poetry run vault export obsidian

# Run tests
poetry run pytest tests/ -v
```

## Architecture Overview

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

## Memory Types

ProjectMemento should support more than conversation archive records:

| Type | Description |
|------|-------------|
| Episodic | Meetings, conversations, dated events and interactions |
| Semantic | Durable facts, client context, architectural knowledge and reusable concepts |
| Procedural | Runbooks, implementation steps, workflows and operating procedures |
| Strategic | Decisions, principles, preferences and long-term direction |
| Project state | Current status, blockers, next actions and repo/project summaries |
| Research | Distilled research with source attribution |
| Relationship | Links between people, clients, systems, repositories and decisions |

## Documentation

| Document | Description |
|----------|-------------|
| [Universal Memory Layer](docs/architecture/universal-memory-layer.md) | New target architecture: shared memory bus, local retrieval and Obsidian visible brain |
| [Development Playbook](docs/playbooks/development.md) | Setup, coding standards, testing |
| [Architecture Playbook](docs/playbooks/architecture.md) | System design and data flow |
| [Project Management](docs/playbooks/project-management.md) | Issues, PRs, milestones |
| [Security Playbook](docs/playbooks/security.md) | Data security and incident response |
| [Roadmap](ROADMAP.md) | Delivery roadmap for vault, universal memory, API, Obsidian and agent integrations |
| [Phase 1 Plan](docs/intro/PHASE1_DETAILED_PLAN_1.md) | Detailed Phase 1 tasks and milestones |

## AI Readiness

This repo includes AI agent configuration in [.agent/rules.md](.agent/rules.md) and [.agent/workflows/](.agent/workflows/). These guide AI-assisted contributions to follow project conventions.

Future agent work should treat ProjectMemento as a governed memory layer, not only as a conversation archive.

## Contributing

We welcome contributions. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and [docs/playbooks/development.md](docs/playbooks/development.md) for setup instructions.

## Security

For security policy and vulnerability reporting, see [SECURITY.md](SECURITY.md).

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
