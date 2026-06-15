# ProjectMemento Roadmap

ProjectMemento is being repositioned from an encrypted LLM conversation archive into a **universal AI memory layer** for Richard's personal WorkOS, local AI stack, GitHub project estate, and reusable client-agent-appliance architecture.

The new delivery path keeps the original secure local vault foundation, but extends it into a governed memory bus where Claude, Codex, ChatGPT, Perplexity, n8n and other tools can write durable memories, while LM Studio, Ollama, Open WebUI, Claude Code workers, FlowFinder and local agents can retrieve approved context.

## Phase 0: Vision Reset & Architecture Alignment — Current

- [x] Reposition ProjectMemento as a universal AI memory layer
- [x] Add universal memory layer architecture document
- [x] Update README with memory-bus, local-reader and Obsidian-visible-brain direction
- [x] Update roadmap to reflect the new target state
- [ ] Update architecture playbook with canonical memory-bus model
- [ ] Update security playbook with namespace, approval, retention and cross-client isolation controls
- [ ] Create implementation task list for Phase 1 rebuild

**Deliverable:** Repository documentation clearly states what ProjectMemento should become.

## Phase 1: Secure Local Vault Foundation

Keep the original foundation because it remains essential.

- [x] Repository scaffolding and AI readiness
- [x] Poetry project with all dependencies (`pyproject.toml`)
- [x] Pydantic configuration models and pre-commit hooks
- [x] SQLAlchemy ORM models and migration system
- [x] Argon2id key derivation and Fernet encryption
- [x] Encrypted blob storage
- [x] Minimal deterministic JSONL memory backend and `vault init` CLI command
- [x] Canonical staged-memory models and CLI commands: `memory stage`, `memory list`, `memory show`, `memory approve`, `memory reject`, `memory search`
- [x] SQLite-backed shared memory layer (`src/memento/`) with Memory, Fact, Preference, Session models
- [x] Python API (`MementoAPI`) for storing/retrieving memories
- [x] Systemd timer/service definitions for periodic memory consolidation
- [ ] Session token management
- [ ] Base ingestion adapter and ChatGPT JSON adapter
- [ ] Import pipeline with deduplication
- [ ] CLI commands: `import`, `list`, `show`, `stats` for conversation vault records
- [ ] Error handling and edge case coverage

**Deliverable:** Import ChatGPT/LLM exports into encrypted local storage with searchable metadata.

## Phase 2: Canonical Memory Schema & Governance Lifecycle

Move beyond conversations into durable memory records.

- [ ] Define canonical memory schema: type, namespace, sensitivity, title, summary, source, confidence, status, retention, tags, links, body and audit metadata
- [ ] Add memory classes: episodic, semantic, procedural, strategic, project_state, research and relationship
- [ ] Add lifecycle states: staged, approved, superseded, rejected and expired
- [ ] Add memory approval workflow via CLI first
- [ ] Add duplicate/similarity detection before approval
- [ ] Add source attribution model for Claude, Codex, ChatGPT, Perplexity, n8n, GitHub, Obsidian and manual notes
- [ ] Add audit log for every create, update, approve, reject, export and delete event

**Deliverable:** Agents and humans can create staged memories; approved memories become retrievable canonical knowledge.

## Phase 3: Security, Sanitisation & Namespace Isolation

Strengthen the system for personal, client and enterprise-adjacent use.

- [ ] PII detection engine using Presidio pattern-based detection and LLM Guard NER
- [ ] YAML-driven policy engine for namespaces, sensitivity levels and allowed operations
- [ ] Client namespace model: personal, public, client/lily, client/helpdesq, client/ricambio and future clients
- [ ] Cross-client retrieval prevention
- [ ] Token vault with encryption
- [ ] Retention and forgetting policy
- [ ] Export policy controlling which memories can sync to Obsidian
- [ ] Adversarial input testing
- [ ] Local-only embedding mode for restricted memories

**Deliverable:** Memories are separated, governed, auditable and safe enough for client-specific knowledge without cross-contamination.

## Phase 4: Retrieval, Context Packs & Local Model Access

Make the memory usable by local models and local agents.

- [ ] Qdrant or pgvector collection setup
- [ ] Local embedding generation using sentence-transformers or equivalent
- [ ] Hybrid search: keyword, metadata, BM25-style and vector search
- [ ] Metadata filtering by namespace, sensitivity, type, project, client and date
- [ ] Retrieval API route for approved memories
- [ ] Context-pack generator for projects, clients and tasks
- [ ] Read-only local agent integration pattern for LM Studio, Ollama and Open WebUI
- [ ] Prompt-ready compact context pack format
- [ ] Performance benchmarking

**Deliverable:** Local models and agents can query approved memory and receive task-relevant context safely.

## Phase 5: Write API & Agent Integration

Allow cloud and coding agents to write memory through governed interfaces.

- [ ] FastAPI write endpoint for staged memories
- [ ] API authentication and rate limiting
- [ ] Writer profiles for Claude, Codex, ChatGPT, Perplexity, n8n, GitHub and manual tools
- [ ] Claude Code post-task summary writer pattern
- [ ] Codex implementation/review summary writer pattern
- [ ] GitHub commit/PR summary ingestion pattern
- [ ] n8n workflow example for email/meeting/voice-note summaries
- [ ] Confidence scoring and policy checks at write time
- [ ] Admin review queue endpoint

**Deliverable:** Trusted tools can write to a memory staging inbox without bypassing governance.

## Phase 6: Obsidian Visible Brain

Make the AI memory human-readable, graphable and curatable.

- [ ] Define Obsidian vault folder structure
- [ ] Define markdown export format and YAML front matter
- [ ] Add one-way exporter: ProjectMemento -> Obsidian markdown mirror
- [ ] Add Dataview-compatible properties
- [ ] Add relationship links between clients, projects, repos, tools, decisions and memories
- [ ] Add staged-memory review notes in `00-Inbox/`
- [ ] Add export rules by namespace/sensitivity/status
- [ ] Add optional Obsidian-to-staging import for notes marked `memento_ingest: true`

**Deliverable:** Richard can see and browse the AI brain in Obsidian while ProjectMemento remains the canonical memory core.

## Phase 7: Production Deployment & Operations

Harden for Richard's local infrastructure and future reusable appliances.

- [ ] Local workstation deployment profile
- [ ] Proxmox VM/LXC deployment profile
- [ ] Optional client-agent-appliance deployment profile
- [ ] Monitoring with Prometheus and Grafana
- [ ] Backup automation and restore workflows
- [ ] Health checks for database, vector store, API, exporter and ingestion queue
- [ ] Operational runbooks
- [ ] Upgrade/migration playbook
- [ ] Documentation for admin mode vs user mode

**Deliverable:** Production-ready ProjectMemento deployment on Richard-controlled infrastructure.

## Phase 8: Advanced Memory Intelligence

Add higher-order capability after the core system is trustworthy.

- [ ] Automatic memory consolidation and summarisation
- [ ] Supersession detection for outdated memories
- [ ] Relationship graph extraction
- [ ] Optional Neo4j or graph-table backend
- [ ] Memory quality scoring
- [ ] Scheduled review reminders
- [ ] Cross-repo project-state packs
- [ ] Multi-agent shared working memory for WorkOS use cases
- [ ] Mem0 interoperability or embedded Mem0 adapter if useful

**Deliverable:** ProjectMemento becomes an intelligent, self-maintaining memory layer rather than a passive store.

## Current Priority

The immediate priority is **Phase 0 -> Phase 2**:

1. Finish documentation alignment.
2. Define the canonical memory schema.
3. Build staged-memory creation and approval.
4. Keep storage local-first and encrypted.
5. Add the first simple retrieval path for local agents.
6. Add the first one-way Obsidian export.

The guiding rule: **write governance first, retrieval second, automation third.**
