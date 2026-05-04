# ProjectMemento Universal Memory Layer

## Purpose

ProjectMemento should evolve from a local conversation archive into a shared, governed memory layer for Richard's full AI operating environment.

The system should act as a **central memory bus** where trusted cloud tools, local models, local agents, repositories, notes, and automation systems can all contribute to and retrieve from a common knowledge substrate.

In practical terms:

- Claude, Codex, ChatGPT, Perplexity, browser agents, and n8n workflows can **write** durable knowledge into ProjectMemento.
- LM Studio, Ollama, Open WebUI, local agents, Claude Code workers, FlowFinder, and client appliances can **read** from ProjectMemento.
- Obsidian can mirror selected memory records as a human-readable, browsable, graphable second brain.
- The same system can support personal work, GitHub project work, consulting delivery, and reusable client-agent appliances without every model having a different fragmented memory.

## North Star

ProjectMemento becomes the **shared memory substrate for human + multi-agent collaboration**.

It is not just an LLM export vault. It is the place where validated context, decisions, project state, client knowledge, procedures, research outputs, and reusable lessons are distilled, governed, and made available to whichever model or agent needs them.

## Design Principles

1. **Local-first by default**
   - The authoritative store runs locally or on Richard-controlled infrastructure.
   - External/cloud LLMs may write through controlled APIs, but the memory store remains under local control.

2. **Human-visible brain**
   - Important memory should not disappear into a vector database only an agent can inspect.
   - Obsidian markdown export provides a readable, editable, graphable mirror of selected knowledge.

3. **Model-agnostic memory**
   - Claude, Codex, GPT, local Llama/Mistral/Qwen models, n8n agents, and future tools should all access the same memory through stable interfaces.

4. **Write governance before autonomy**
   - Cloud and autonomous agents should initially write to an inbox/staging area.
   - Human approval, confidence scoring, deduplication, and source attribution should protect the long-term memory store.

5. **Client and sensitivity separation**
   - Personal, public, client-safe, client-confidential, and restricted memories must be separated by namespace and policy.
   - HelpDesQ, Lily's Kitchen, Ricambio, and future client pilots should never cross-contaminate memory.

6. **Source-linked and reversible**
   - Every memory should include source, authoring agent, creation time, confidence, namespace, and retention policy.
   - Memories should be supersedable, revocable, and forgettable.

7. **Readable + retrievable**
   - Store both structured metadata and natural language summaries.
   - Retrieval should support semantic search, keyword search, tags, time filters, project/client filters, and relationship traversal.

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
       │ authentication, policy, staging inbox  │
       │ redaction, dedupe, confidence scoring  │
       └───────────────────┬────────────────────┘
                           │
                           ▼
                  ProjectMemento Memory Core
       ┌────────────────────────────────────────┐
       │ Canonical memory records               │
       │ SQLite/Postgres metadata               │
       │ encrypted blob store                   │
       │ Qdrant or pgvector embeddings          │
       │ optional graph index                   │
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

## Core Memory Types

ProjectMemento should support multiple memory classes rather than treating everything as a conversation.

| Type | Description | Example |
| --- | --- | --- |
| Episodic memory | Event, meeting, conversation, or dated interaction | "HelpDesQ discovery identified Kronos as SQL-backed source of truth." |
| Semantic memory | Durable fact or concept | "Ricambio uses Shopify, Sparklayer, Unleashed, and PRYSYNK." |
| Procedural memory | Reusable process or runbook | "How to create a Zendesk Auto Assist procedure from a Word document." |
| Strategic memory | Decisions, preferences, architectural principles | "Prefer local-first, modular, human-in-the-loop agent designs." |
| Project state | Current status, next actions, blockers, commit notes | "client-agent-appliance needs a generic reusable VM template dashboard." |
| Research memory | Distilled research output with citations/source references | "Cloudflare Agent Memory validates managed memory-as-a-service pattern." |
| Relationship memory | Links between people, clients, systems, repos, and decisions | "Lily's Kitchen -> NetSuite -> Boomi -> Azure Fabric migration." |

## Memory Record Shape

A v1 canonical memory record should contain at least:

```yaml
id: mem_...
type: semantic | episodic | procedural | strategic | project_state | research | relationship
namespace: personal | public | client/lily | client/helpdesq | client/ricambio | system
sensitivity: public | internal | client_confidential | restricted
title: Short human-readable title
summary: Distilled memory text
source:
  system: claude | codex | chatgpt | perplexity | n8n | github | obsidian | manual
  uri: optional source URL, repo path, commit, message, export id, or note path
  captured_at: ISO-8601 timestamp
confidence: 0.0-1.0
status: staged | approved | superseded | rejected | expired
retention: keep | review | expire | delete_after_date
tags: [client, project, tool, topic]
links:
  related_memory_ids: []
  related_repos: []
  related_obsidian_notes: []
body: Full optional source-derived content or expanded note
audit:
  created_by: agent/user id
  approved_by: optional human id
  updated_at: ISO-8601 timestamp
```

## Write Model

### Phase 1 Write Pattern

All non-human writers should initially write to a **staging inbox**.

```text
Agent output -> Write API -> staged memory -> review/dedupe -> approved memory -> retrieval index + Obsidian mirror
```

This prevents the memory store becoming an untrusted dumping ground.

### Writers

Likely writer integrations:

- Claude Code post-task summaries
- Codex implementation summaries and code review findings
- ChatGPT strategy conversations manually exported or pushed via API
- Perplexity research summaries with source links
- GitHub commit/PR summaries
- n8n automations from email, meeting notes, voice notes, or repo changes
- Obsidian notes intentionally marked for ingestion

### Write Controls

Each write should be governed by:

- namespace allow-list
- sensitivity classification
- source attribution
- PII/confidential data policy
- duplicate/similarity detection
- summarisation quality checks
- human approval for client-confidential or high-impact strategic memories

## Read Model

Local models and agents should not need to know the storage internals. They should query a retrieval API.

Example query modes:

- `search`: semantic + keyword search across allowed namespaces
- `context_pack`: return a compact prompt-ready context pack for a project/client/task
- `facts`: return approved semantic memories only
- `procedures`: return approved procedural/runbook memories
- `timeline`: return episodic memories in date order
- `relationships`: return linked entities and memory graph edges

Example consumers:

- LM Studio RAG tools
- Ollama agents
- Open WebUI knowledge integrations
- Claude Code local workers
- FlowFinder
- Client-agent-appliance deployments
- GitHub repo automation agents
- Personal WorkOS dashboard

## Obsidian Mirror

Obsidian should be treated as the **human-facing cortex**, while ProjectMemento remains the machine-facing memory core.

### Recommended folder structure

```text
ProjectMemento-Obsidian-Vault/
├── 00-Inbox/
│   ├── Staged-Memories/
│   └── Needs-Review/
├── 10-Clients/
│   ├── Lily-Kitchen/
│   ├── HelpDesQ/
│   └── Ricambio/
├── 20-Projects/
│   ├── Client-Agent-Appliance/
│   ├── FlowFinder/
│   ├── Local-AI-Assistant-MVP/
│   └── Claude-Local-Agents/
├── 30-Knowledge/
│   ├── AI-Architecture/
│   ├── Security-Governance/
│   ├── Agentic-Workflows/
│   └── Tooling-Research/
├── 40-Procedures/
├── 50-Decisions/
├── 60-Relationships/
└── 90-Archive/
```

### Markdown front matter

```yaml
---
memento_id: mem_...
type: semantic
namespace: client/helpdesq
sensitivity: client_confidential
status: approved
confidence: 0.86
tags: [helpdesq, kronos, trinity, sql, msp]
source_system: claude
source_uri: github:repo/path-or-session-id
created: 2026-05-04T00:00:00Z
updated: 2026-05-04T00:00:00Z
---
```

### Sync direction

Start with **one-way export**:

```text
ProjectMemento -> Obsidian markdown mirror
```

Then add controlled two-way sync later:

```text
Obsidian note with memento_ingest: true -> staging inbox -> approval -> canonical memory
```

Obsidian should not be allowed to silently overwrite canonical memory records without review.

## Storage Options

The current local-first design can remain valid, but the longer-term memory bus likely needs a slightly richer deployment profile.

### MVP

- SQLite for metadata
- encrypted blob store for full content
- Qdrant for embeddings
- local sentence-transformers for embeddings
- FastAPI retrieval/write API
- markdown exporter to Obsidian

### Scalable local appliance

- Postgres for metadata
- pgvector or Qdrant for embeddings
- Redis for cache/session state
- optional Neo4j or graph table for entity relationships
- Prometheus/Grafana for health and ingestion metrics

## Relationship to Mem0

Mem0 can be used in one of three ways:

1. **Reference pattern only**
   - Keep ProjectMemento custom and use Mem0 as inspiration for extraction, retrieval, and lifecycle patterns.

2. **Embedded component**
   - Use Mem0 as the memory extraction/retrieval library under ProjectMemento's governance, storage, and Obsidian sync layers.

3. **Interoperability target**
   - Implement compatible APIs or adapters so ProjectMemento can import/export Mem0-style memory records.

Recommended v1 approach: **do not surrender the whole architecture to Mem0**. Use Mem0 as a useful component or reference, but keep ProjectMemento as the governed, local-first memory operating layer.

## Security and Governance

Minimum controls:

- per-namespace access control
- per-client isolation
- encryption at rest
- local embedding option for sensitive content
- redaction/sanitisation pipeline before external LLM processing
- audit log for every write, update, approval, export, and delete
- memory status lifecycle: staged -> approved -> superseded/rejected/expired
- retention and forgetting policy
- export policy controlling what may appear in Obsidian
- no automatic cross-client retrieval

## V1 Success Criteria

A successful v1 should demonstrate:

1. Claude/Codex/ChatGPT-style outputs can be written into a staging inbox through an API or CLI.
2. A human can approve, edit, reject, or supersede staged memories.
3. Local LM Studio/Ollama agents can retrieve approved memory through a simple read API.
4. Obsidian receives a readable markdown mirror of approved, exportable memories.
5. Client namespaces remain isolated.
6. Every memory has source attribution, status, confidence, tags, and audit metadata.
7. The system can produce project/client context packs for prompt injection or RAG use.

## Immediate Build Priorities

1. Define canonical memory schema.
2. Add write API/CLI for staged memory creation.
3. Add approval workflow.
4. Add retrieval API for local models and agents.
5. Add Obsidian markdown exporter.
6. Add namespace/sensitivity policy file.
7. Add dedupe/similarity checking.
8. Add context-pack generation.
9. Add audit log and retention rules.
10. Add deployment profile for local workstation, Proxmox, and client-agent-appliance use.
