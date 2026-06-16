# Phase 1 Foundation: Deterministic Local Memory Layer

This document records the intentionally minimal Phase 1 foundation delivered for
ProjectMemento issue `#7`.

## Scope

Phase 1 now has a small local memory layer that can be used by humans, Claude,
Codex or other managed agents without running a daemon:

- canonical memory request/record models in `vault.memory`;
- deterministic memory IDs derived from stable SHA-256 content hashes;
- a local JSONL file backend at `vault_data/memory/memories.jsonl`;
- CLI commands for `init`, `memory stage`, `memory list`, `memory show`,
  `memory approve`, `memory reject` and `memory search`;
- governed retrieval: `memory search` returns approved records only unless
  `--include-staged` is explicitly passed;
- fail-closed sensitivity default: missing sensitivity becomes `restricted`;
- client namespaces require `client_confidential` or `restricted` sensitivity.

This is not the full long-term daemon, vector search, API, Obsidian exporter or
encrypted blob design. It is the smallest deterministic layer that lets planned
agents begin writing managed memory proposals locally.

## Memory input shape

`vault memory stage` accepts YAML or JSON:

```yaml
type: project_state
namespace: project/projectmemento
sensitivity: internal
title: Phase 1 foundation started
summary: ProjectMemento now has a deterministic local memory layer.
source:
  system: codex
  uri: ProjectMemento#7
confidence: 0.8
tags:
  - phase-1
  - memory
body: Optional longer local-only detail.
created_by: codex
```

Supported memory types:

- `episodic`
- `semantic`
- `procedural`
- `strategic`
- `project_state`
- `research`
- `relationship`

Supported statuses:

- `staged`
- `approved`
- `superseded`
- `rejected`
- `expired`

Supported sensitivity values:

- `public`
- `internal`
- `client_confidential`
- `restricted`

Allowed root namespaces are `personal`, `public`, `system`, `project` and
`client`. Client namespaces such as `client/helpdesq` deliberately reject
`public` and `internal` records.

## CLI examples

```bash
poetry run vault init
poetry run vault memory stage memory.yaml
poetry run vault memory list --status staged
poetry run vault memory show mem_<id>
poetry run vault memory approve mem_<id> --approved-by richard
poetry run vault memory search "phase foundation" --namespace project/projectmemento
```

Use `--root /path/to/vault_data` on any command to keep test or agent-specific
stores isolated.

## Activation tier and future timer/service path

The target activation tier for bringing planned agents under management is
approximately **18 timer/service**: enough automation to run routine memory
capture, review prompts, exports and health checks, but still below the point
where ProjectMemento becomes an always-on autonomous writer.

Recommended progression:

1. **Manual CLI first** — agents write YAML/JSON proposals and call
   `vault memory stage`; Richard approves or rejects locally.
2. **Repository/task hooks** — Claude/Codex task wrappers stage summaries after
   implementation or review, still requiring human approval.
3. **User-level systemd timers** — add narrowly scoped timers for jobs such as
   daily staged-memory reports, approved-memory export and backup checks.
4. **User-level systemd services** — only after CLI workflows are stable, wrap
   retrieval/API components as services.
5. **Daemon/API later** — FastAPI, vector search, Obsidian sync and policy
   engines should build on this contract rather than bypassing it.

A future systemd timer path should keep units in documentation or packaging
until the daemon exists, for example:

```text
~/.config/systemd/user/projectmemento-staged-report.timer
~/.config/systemd/user/projectmemento-staged-report.service
~/.config/systemd/user/projectmemento-obsidian-export.timer
~/.config/systemd/user/projectmemento-obsidian-export.service
```

Each timer should call explicit CLI commands, log to a local file and avoid
approving memory automatically. Autonomy can schedule review, retrieval and
export; it must not silently promote staged memories.

## Design notes

- JSONL is used for deterministic, diffable Phase 1 storage.
- The record ID is `mem_` plus the first 16 characters of a SHA-256 hash over
  stable semantic fields.
- Exact duplicate staging is rejected by ID.
- The safe JSON display hides `body` unless `--include-body` is used.
- Later encrypted blob storage can replace plaintext `body` persistence while
  preserving the CLI and model contract.
