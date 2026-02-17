# Opus Review — Task Assignments, Build Order & Gantt Chart

**Reviewer:** Claude Opus 4.6 (Claude Code)
**Date:** 2026-02-17
**Scope:** Phase 1 task dispatch, model capability matching, dependency integrity, build order

---

## 1. Task Assignment Review

### Assessment Criteria

Each task is evaluated against the assigned model's known capabilities:

| Capability | Local 3B | Haiku | Sonnet | Opus | Copilot | Perplexity |
|-----------|----------|-------|--------|------|---------|------------|
| Boilerplate/scaffolding | Good | Good | Good | Good | Good | N/A |
| Dataclass/Protocol defs | Moderate | Good | Good | Good | Good | N/A |
| SQL/ORM queries | Poor | Moderate | Good | Good | Moderate | N/A |
| Crypto/security logic | Poor | Poor | Good | Excellent | Poor | N/A |
| Complex parsing (trees) | Poor | Moderate | Good | Excellent | Moderate | N/A |
| Test case generation | Moderate | Good | Good | Good | Good | N/A |
| Multi-file integration | Poor | Moderate | Good | Excellent | Poor | N/A |
| CLI wiring (Typer/Rich) | Moderate | Good | Good | Good | Good | N/A |
| Research | N/A | N/A | N/A | N/A | N/A | Excellent |

### Task-by-Task Verdict

| Task | Assigned To | Verdict | Notes |
|------|------------|---------|-------|
| **1.3.1 crypto.py** | Sonnet (done by Opus) | CORRECT | Security-critical. Argon2id + HKDF requires understanding of crypto primitives. Local LLMs would hallucinate params. |
| **1.3.2 blobs.py** | Sonnet (done by Opus) | CORRECT | Atomic writes, secure deletion, sharded paths — needs reliability guarantees local models can't provide. |
| **1.5.1 session.py** | Sonnet (done by Opus) | CORRECT | Token hashing, constant-time comparison, HKDF key derivation — security-critical. |
| **1.2.2 migrations.py** | Local LLM (Qwen/DeepSeek) | CAUTION | Simple concept but requires understanding SQLAlchemy engine + raw SQL interplay. **Recommendation:** Keep assigned but ensure the task file gives explicit SQL strings (which it does). Acceptable. |
| **1.6.1 base adapter** | Local LLM (Qwen/DeepSeek) | CORRECT | Pure dataclasses + Protocol — no external dependencies, no complex logic. Ideal for 3B models. Well-specified in task file. |
| **D0 test scaffolding** | Local LLM (Llama 3B) | CORRECT | Creating empty files + simple fixtures. Perfect for the weakest model. Task file is explicit enough. |
| **D0 research** | Perplexity | CORRECT | Research is Perplexity's strength. Three focused queries. |
| **1.4.1 db.py (VaultDB)** | Gemini/Haiku | CAUTION | SQLAlchemy 2.x `select()` style + WAL pragma events + context managers. This is moderate-complex. **Recommendation:** Assign to Sonnet if using cloud Claude, or Gemini (which handles SQLAlchemy well). Haiku alone may produce bugs in the pragma event listener or session scoping. |
| **1.6.2 chatgpt.py** | Sonnet | CORRECT | Parsing the ChatGPT mapping tree is genuinely complex — nested dict traversal, null handling, multi-part content, role mapping. Requires Tier 3 minimum. |
| **1.4.2 vault init CLI** | Sonnet | CORRECT | Orchestrates crypto + blobs + db initialization. Multi-module integration needs Tier 3. |
| **1.5.2 session CLI wiring** | Haiku | CORRECT | Wiring existing SessionManager into existing CLI helper. Straightforward if the helper function signature is clear. Task should specify exact function to modify. |
| **1.8.1 import pipeline** | Sonnet | CORRECT | Orchestrates adapter→encrypt→store with per-conversation transactions, error recovery, dedup. Complex integration — Tier 3 required. |
| **1.8.2 vault import CLI** | Haiku | CORRECT | CLI wrapper around pipeline with Rich progress bar. Haiku can handle this with a clear task file. |
| **1.9.1 vault list** | Local LLM/Copilot | CORRECT | Simple Rich table + db query. Well-specified. |
| **1.9.2 vault show** | Haiku | CORRECT | Decrypt + display. Moderate but well-bounded. |
| **1.9.3 vault stats** | Local LLM/Copilot | CORRECT | Simple Rich panel + aggregate queries. Well-specified. |
| **1.9.4 error polish** | Haiku | CORRECT | Try/except wrappers + user-facing messages. Haiku's sweet spot. |
| **Unit tests** | Haiku | CORRECT | Test generation from existing code is Haiku's strength. Cost-effective. |
| **Integration tests** | Sonnet | CORRECT | Full workflow testing requires understanding of all modules. Tier 3. |
| **Security review** | Opus | CORRECT | Final security audit is Opus-tier work. Critical for a privacy/encryption product. |

### Summary of Recommended Changes

1. **TASK-1.4.1 (db.py):** Prefer Gemini or Sonnet over Haiku. The SQLAlchemy pragma event listener and WAL mode setup are easy to get wrong. Mark Haiku as fallback only.
2. **TASK-1.2.2 (migrations.py):** Acceptable for local LLMs given the explicit SQL in the task file, but consider having Haiku review the output before merging.
3. **All other assignments:** Confirmed appropriate.

---

## 2. Build Order Verification

### Dependency Chain Analysis

```
VERIFIED DEPENDENCY GRAPH:

crypto.py ──────┬──► blobs.py ──────┬──► vault init CLI ──► session CLI ──► import CLI
                │                   │
                ├──► session.py     │
                │                   │
migrations.py ──► db.py ───────────┘
                                    │
base adapter ──► chatgpt.py ───────►├──► import pipeline ──► vault import CLI
                                    │
                                    ├──► vault list
                                    ├──► vault show
                                    └──► vault stats
```

### Verified Constraints

| Constraint | Status | Reason |
|-----------|--------|--------|
| crypto.py before blobs.py | DONE | blobs.py imports KeyManager for Fernet encryption |
| crypto.py before session.py | DONE | session.py uses HKDF from cryptography (same pattern) |
| migrations.py before db.py | CORRECT | db.py calls `apply_migrations(engine)` in `init_schema()` |
| base adapter before chatgpt.py | CORRECT | chatgpt.py implements BaseAdapter Protocol, returns ParsedConversation |
| blobs.py + db.py before vault init | CORRECT | init creates blob dir structure + initializes DB schema |
| vault init before session CLI | CORRECT | session CLI needs an initialized vault to work with |
| chatgpt.py + db.py + blobs.py before pipeline | CORRECT | pipeline orchestrates all three |
| pipeline before vault import CLI | CORRECT | CLI wraps pipeline |
| db.py before list/show/stats | CORRECT | all query the database |

### Best Practice Checks

| Practice | Status | Detail |
|---------|--------|--------|
| Security modules built first | PASS | crypto.py was built first, all other modules depend on it |
| No circular dependencies | PASS | Strict layered architecture: security → storage → ingestion → CLI |
| Tests parallel to implementation | PASS | Test scaffolding in Layer 0, unit tests in Layer 1-2 |
| Integration tests last | PASS | Layer 5, after all modules exist |
| Security review before release | PASS | Opus review in Layer 3, before final assembly |
| CLI built on top of library | PASS | All business logic in modules, CLI is thin wrapper |
| Database abstraction layer | PASS | VaultDB wraps SQLAlchemy, CLI never touches engine directly |

### Issues Found: None

The build order is sound. The critical path is:

```
crypto → blobs → (db in parallel) → vault init → session CLI → pipeline → import CLI → commands → polish
```

This is the minimum sequential chain. Everything else runs in parallel without adding elapsed time.

---

## 3. Gantt Chart

```
PHASE 1 — GANTT CHART (Time flows left to right)
═══════════════════════════════════════════════════════════════════════════════

LAYER 0 (Parallel kickoff)                          LAYER 1             LAYER 2          LAYER 3           LAYER 4
Day 1              Day 2              Day 3          Day 4              Day 5             Day 6             Day 7-8
├──────────────────┼──────────────────┼──────────────┼──────────────────┼─────────────────┼─────────────────┼────────────────┤

CLAUDE CODE (ai/feat-core-infrastructure):
████████████████████                                                                                         crypto.py [DONE]
                    ████████████████████                                                                     blobs.py [DONE]
                    ████████████████████                                                                     session.py [DONE]
                                        ██████████████████████████                                           chatgpt.py
                                                      ████████████████████                                   vault init CLI
                                                                        ██████████████████████████████       import pipeline
                                                                                                    ████    integration tests

LOCAL LLMs (ai/feat-local-scaffolding):
████████                                                                                                     test scaffolding
████████████████████                                                                                         migrations.py
████████████████████                                                                                         base adapter
                                                                        ████████                             vault list
                                                                        ████████                             vault stats

CLOUD CLAUDE (ai/feat-cloud-tasks):
                                        ██████████████████████████                                           db.py (after migrations)
                                        ████████████████████                                                 unit tests (L0)
                                                      ████████████████████                                   session CLI wiring
                                                      ████████████████████                                   unit tests (L1)
                                                                        ██████████████████████████████       vault import CLI
                                                                        ████████████████████                 vault show
                                                                                          ████████████████   error polish

PERPLEXITY:
████████                                                                                                     research x3

OPUS:
                                                                        ████████████████████                  security review

═══════════════════════════════════════════════════════════════════════════════

LEGEND:
████  = Active work period
[DONE] = Completed in this session
```

### Parallel Swim Lane Summary

| Platform | Layer 0 | Layer 1 | Layer 2 | Layer 3 | Layer 4 |
|---------|---------|---------|---------|---------|---------|
| **Claude Code** | crypto [DONE], blobs [DONE], session [DONE] | chatgpt.py | vault init | pipeline | integration tests |
| **Local LLMs** | scaffolding, migrations, base adapter | — | — | list, stats | — |
| **Cloud Claude** | — | db.py, unit tests (L0) | session CLI, unit tests (L1) | import CLI, show | error polish |
| **Perplexity** | research x3 | — | — | — | — |
| **Opus** | — | — | — | security review | — |

### Critical Path Duration

The critical path determines minimum elapsed time regardless of parallelization:

```
crypto (DONE) → blobs (DONE) → chatgpt.py (~3h) → vault init (~2h) → pipeline (~3h) → import CLI (~1h) → polish (~1h)
                                                     ↑
                                            db.py must also be done (parallel path)
```

**Estimated remaining critical path: ~10 hours of focused work across 2-3 sessions.**

---

## 4. Recommendations for Next Session (Cloud Claude)

### Immediate Actions for Cloud Claude on Mobile

1. **Pick up TASK-1.4.1 (db.py)** — This is on the critical path. Use Sonnet. Dependencies (migrations.py) can be mocked if local LLMs haven't finished it yet, but ideally wait for it.

2. **Write unit tests for crypto.py, blobs.py, session.py** — These modules are complete and stable. Haiku can generate tests from the existing code. No dependencies needed.

3. **Create TASK-1.6.2-chatgpt-adapter.md** — An instruction file for the ChatGPT adapter doesn't exist yet. Claude Code should build this directly (Sonnet tier), but cloud Claude can help research the ChatGPT export format first.

### Work Distribution for Next Session

| Priority | Task | Model | Branch |
|----------|------|-------|--------|
| 1 | Unit tests for crypto/blobs/session | Haiku | ai/feat-cloud-tasks |
| 2 | db.py (VaultDB wrapper) | Sonnet | ai/feat-cloud-tasks |
| 3 | ChatGPT adapter research | Any | ai/feat-cloud-tasks |

---

## 5. Document Currency Check

| Document | Current? | Action Needed |
|---------|----------|---------------|
| CLAUDE.md | Yes | Update after this commit |
| CHANGELOG.md | Yes | Already covers M1.1-1.3 |
| SESSION_SUMMARY_2026-02-17.md | Needs update | Add Session 3 (this review) |
| docs/tasks/README.md | Yes | Task statuses current |
| ROADMAP.md | Not checked | Should verify alignment |
| docs/intro/PHASE1_DETAILED_PLAN_1.md | Yes | Master plan, read-only reference |

---

*Review complete. All task assignments verified. Build order confirmed sound. No blocking issues found.*
