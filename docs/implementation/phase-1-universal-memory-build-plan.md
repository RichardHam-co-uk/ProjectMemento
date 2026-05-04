# Phase 1 Universal Memory Build Plan

This build plan translates the new ProjectMemento direction into practical implementation work for Claude Code, Codex or a human developer.

The objective is to move from an encrypted conversation vault toward a governed universal memory layer where:

- cloud/coding agents can write proposed memories into a staging inbox;
- Richard can approve, edit, reject or supersede those memories;
- local models and agents can retrieve approved memories;
- approved exportable memory can be mirrored into Obsidian.

## Guiding Rule

Build in this order:

1. **Schema**
2. **Governed write/staging**
3. **Approval lifecycle**
4. **Read/retrieval**
5. **Obsidian mirror**
6. **Automation integrations**

Do not build autonomous write-to-approved-memory behaviour before governance is working.

## Workstream 1: Canonical Memory Schema

### Goal

Create a first-class memory record separate from raw imported conversations.

### Tasks

- [ ] Add `vault/memory/` package.
- [ ] Define memory type enum:
  - `episodic`
  - `semantic`
  - `procedural`
  - `strategic`
  - `project_state`
  - `research`
  - `relationship`
- [ ] Define memory status enum:
  - `staged`
  - `approved`
  - `superseded`
  - `rejected`
  - `expired`
- [ ] Define sensitivity enum:
  - `public`
  - `internal`
  - `client_confidential`
  - `restricted`
- [ ] Define namespace model:
  - `personal`
  - `system`
  - `public`
  - `client/lily`
  - `client/helpdesq`
  - `client/ricambio`
  - `client/<name>`
- [ ] Add Pydantic model for incoming staged memory request.
- [ ] Add SQLAlchemy model for canonical memory metadata.
- [ ] Add encrypted blob pointer for optional full body/source content.
- [ ] Add migration/init behaviour.
- [ ] Add unit tests for validation.

### Acceptance Criteria

- Invalid memory type/status/sensitivity values are rejected.
- Missing sensitivity defaults to `restricted` or fails closed.
- Memory records can be created in `staged` state.
- Full body/source content is not stored as plaintext by default.

## Workstream 2: Staged Write CLI

### Goal

Let Claude Code, Codex or a human process create staged memory records without needing the API first.

### Proposed Commands

```bash
poetry run vault memory stage memory.yaml
poetry run vault memory list --status staged
poetry run vault memory show mem_123
```

### Tasks

- [ ] Add `vault memory stage <file>` command.
- [ ] Support YAML and JSON staged memory input.
- [ ] Validate required metadata.
- [ ] Run policy checks before storing.
- [ ] Store record as `staged`.
- [ ] Add `memory list` filters by status, namespace, type and sensitivity.
- [ ] Add `memory show` with safe display mode.
- [ ] Add tests and sample staged memory files.

### Acceptance Criteria

- A Claude/Codex-generated YAML memory can be staged locally.
- The command refuses unknown namespaces unless explicitly configured.
- Sensitive body content is encrypted or omitted from plaintext output.

## Workstream 3: Approval Lifecycle

### Goal

Make the staging inbox useful and safe.

### Proposed Commands

```bash
poetry run vault memory approve mem_123
poetry run vault memory reject mem_123 --reason "duplicate"
poetry run vault memory supersede mem_123 --by mem_456
poetry run vault memory expire mem_123
```

### Tasks

- [ ] Add approve command.
- [ ] Add reject command with reason.
- [ ] Add supersede command linking old/new memories.
- [ ] Add expire command.
- [ ] Add audit events for lifecycle changes.
- [ ] Prevent retrieval of non-approved records by default.
- [ ] Add tests for lifecycle transitions.

### Acceptance Criteria

- Staged memories do not appear in default retrieval.
- Approval changes status and writes audit entry.
- Rejected/superseded/expired memories remain traceable.

## Workstream 4: Dedupe and Conflict Detection

### Goal

Avoid building an AI hoarder brain full of duplicated or contradictory memories.

### Tasks

- [ ] Add content hash for exact duplicate detection.
- [ ] Add similarity check against existing approved/staged summaries.
- [ ] Add possible-duplicate warning at staging time.
- [ ] Add possible-supersession workflow for conflicting records.
- [ ] Add CLI flag to list likely duplicates.

### Acceptance Criteria

- Exact duplicate staged writes are blocked or linked.
- Similar proposed memories are flagged for review.
- No silent overwrite of approved memories.

## Workstream 5: Retrieval API and Context Packs

### Goal

Allow local models and agents to retrieve approved memory safely.

### Proposed Commands/API

```bash
poetry run vault memory search "HelpDesQ Kronos billing"
poetry run vault context build --namespace client/helpdesq --topic "billing automation"
```

API routes:

```text
GET /memory/search
POST /context-pack
```

### Tasks

- [ ] Add keyword search over approved summaries and metadata.
- [ ] Add vector search once embeddings are available.
- [ ] Add metadata filters: namespace, sensitivity, type, tag and date.
- [ ] Add caller profile/allowed namespace concept.
- [ ] Add context-pack generator with size/token limits.
- [ ] Return compact prompt-ready output.
- [ ] Add tests for namespace and status filtering.

### Acceptance Criteria

- Retrieval returns approved records only by default.
- Retrieval cannot cross client namespaces unless authorised.
- A local agent can request a compact context pack for a project/client/task.

## Workstream 6: Obsidian One-Way Export

### Goal

Make approved memories visible to Richard in Obsidian.

### Proposed Command

```bash
poetry run vault export obsidian --vault-path ~/Obsidian/ProjectMemento
```

### Tasks

- [ ] Add `vault/export/obsidian.py`.
- [ ] Define folder router by namespace/type/project.
- [ ] Render markdown with YAML front matter.
- [ ] Include `memento_id`, `type`, `namespace`, `sensitivity`, `status`, `confidence`, `tags`, `source_system`, `source_uri`, `created`, `updated`.
- [ ] Add links to related memory notes where possible.
- [ ] Respect export policy:
  - export approved only;
  - never export restricted by default;
  - client confidential only to separated folders if enabled.
- [ ] Add dry-run mode.
- [ ] Add tests for front matter and policy filtering.

### Acceptance Criteria

- Approved internal/public memories export to markdown.
- Restricted memories are skipped by default.
- Obsidian graph can display project/client/tool relationships through links and tags.

## Workstream 7: Writer API

### Goal

Let external agents and automations create staged memory records through a controlled API.

### Tasks

- [ ] Add `POST /memory/stage` endpoint.
- [ ] Add writer API token/profile model.
- [ ] Add rate limiting.
- [ ] Add namespace allow-list per writer.
- [ ] Add sensitivity ceiling per writer.
- [ ] Add audit event for each write attempt.
- [ ] Add example payloads for Claude, Codex, GitHub and n8n.

### Acceptance Criteria

- Claude/Codex/n8n-style clients can stage a memory using an API token.
- Writers cannot write outside their allowed namespaces.
- API writes are staged, not automatically approved.

## Workstream 8: First Integrations

### Goal

Prove the end-to-end pattern with simple integrations before making it sophisticated.

### Initial integrations

1. **Claude Code / Codex summary file**
   - Agent writes a YAML memory summary file after a repo task.
   - CLI stages it.

2. **GitHub commit/PR summary**
   - Script summarises repo changes into project_state memory.
   - Memory is staged for approval.

3. **LM Studio/Ollama read-only context**
   - Local agent queries approved memory by topic/project.
   - Context pack is injected into prompt.

4. **Obsidian export**
   - Approved memories render as markdown.

## Suggested Initial Milestone

### Milestone: Memory Round Trip v0.1

A minimal successful loop:

```text
Claude/Codex creates memory YAML
  -> ProjectMemento stages it
  -> Richard approves it
  -> Local model retrieves it
  -> Obsidian displays it
```

### Demo Scenario

Use a safe internal memory such as:

> ProjectMemento should become a universal memory layer where cloud agents can write, local agents can read, and Obsidian mirrors approved memory as the visible brain.

Expected result:

- staged memory exists;
- approved memory is searchable;
- context pack includes it;
- Obsidian markdown note is generated.

## Non-Goals for This Phase

- Fully autonomous memory approval.
- Complex graph database implementation.
- Production client ingestion using real sensitive data.
- Two-way Obsidian sync.
- Advanced Mem0 integration.
- Direct write-to-approved-memory from cloud agents.

These can follow once the governed memory core works reliably.
