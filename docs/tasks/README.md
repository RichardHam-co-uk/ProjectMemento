# Task Dispatch Board

This directory contains task instruction files for parallel AI-assisted development.
Each file is self-contained with context, requirements, acceptance criteria, and a console prompt.

## How It Works

1. **Pick a task** assigned to your platform (see table below)
2. **Read the instruction file** — it tells you which existing files to read first
3. **Create a branch** from `main`: `git checkout -b ai/<branch-name>`
4. **Build the code** following the requirements
5. **Run checks:** `poetry run pytest`, `poetry run ruff check .`, `poetry run black --check .`
6. **Commit and push** your branch
7. **Mark the task DONE** in this file by changing the status

## Task Status

### Platform: Local LLMs (Continue Extension)
Work on branch: `ai/feat-local-scaffolding`

| Task File | Model | Status | Depends On |
|-----------|-------|--------|------------|
| `TASK-D0-test-scaffolding.md` | Llama3b | TODO | Nothing |
| `TASK-1.2.2-migrations.md` | Qwen/DeepSeek | TODO | Nothing |
| `TASK-1.6.1-base-adapter.md` | Qwen/DeepSeek | TODO | Nothing |
| `TASK-1.9.1-vault-list.md` | Qwen/Copilot | TODO | db.py + CLI must exist |
| `TASK-1.9.3-vault-stats.md` | Qwen/Copilot | TODO | db.py + blobs.py must exist |

### Platform: Cloud Claude (Mobile)
Work on branch: `ai/feat-cloud-tasks`

| Task File | Model | Status | Depends On |
|-----------|-------|--------|------------|
| `TASK-1.4.1-db-wrapper.md` | Haiku/Sonnet | TODO | migrations.py |
| (unit tests — see CLAUDE.md) | Haiku | TODO | modules to test must exist |
| (vault show command) | Haiku | TODO | db.py + blobs.py + CLI |
| (session CLI integration) | Haiku | TODO | session.py + vault init |
| (import CLI command) | Haiku | TODO | pipeline.py + session CLI |
| (error handling polish) | Haiku | TODO | all CLI commands |

### Platform: Claude Code (Local VSCode)
Work on branch: `ai/feat-core-infrastructure`

| Task | Status | Depends On |
|------|--------|------------|
| crypto.py (KeyManager) | DONE | — |
| blobs.py (BlobStore) | DONE | crypto.py |
| session.py (SessionManager) | DONE | crypto.py |
| chatgpt.py (ChatGPTAdapter) | IN PROGRESS | base adapter |
| vault init CLI | TODO | blobs.py + db.py |
| import pipeline | TODO | chatgpt.py + db.py + blobs.py |
| integration tests | TODO | all modules |
| security review | TODO | crypto + blobs + session |

### Platform: Perplexity (Browser)
| Task File | Status |
|-----------|--------|
| `TASK-D0-research.md` (3 queries) | TODO |

## Execution Order

**Start immediately (no dependencies):**
1. Local LLMs: test scaffolding, migrations.py, base adapter
2. Perplexity: all 3 research queries
3. Claude Code: already building critical path

**After Layer 0 completes:**
4. Cloud Claude: db-wrapper (needs migrations.py from local LLMs)
5. Cloud Claude: unit tests (needs modules to exist)

**After Layer 1-2 completes:**
6. Local LLMs: vault list, vault stats
7. Cloud Claude: vault show, session CLI, import CLI, error polish

## Important Rules

- **ONE platform per branch** — don't mix work across branches
- **Read existing files before modifying** — especially `vault/cli/main.py` which multiple tasks touch
- **Don't touch files owned by another platform** — if in doubt, leave it
- **Commit frequently** with conventional commit messages
