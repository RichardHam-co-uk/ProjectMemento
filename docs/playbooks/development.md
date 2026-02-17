# Development Playbook

This document outlines development standards and workflows for Project Memento.

## Environment Setup
- **Required Tools**:
  - Python 3.11+
  - Poetry (dependency management)
  - Git
  - Claude Code CLI (for task execution)
  - Ollama (optional, local LLMs for Tier 1 tasks)
- **Local Config**: Copy `.env.example` to `.env` and fill in secrets.
- **Install Dependencies**:
  ```bash
  poetry install
  poetry run pre-commit install
  ```

## Branching Strategy
We use a trunk-based GitHub Flow with optional release branches:
1. `main` is always production-ready and protected (no direct pushes).
2. Create short-lived branches from `main` using prefixes:
  - `feat/`, `fix/`, `docs/`, `chore/`, `refactor/`, `test/`, `build/`, `ci/`, `ai/`
3. Open a PR to `main` for review and required checks.
4. Merge using "Squash and Merge" to keep history clean.
5. Use `release/*` only for stabilization; `hotfix/*` for urgent fixes, then merge back to `main`.

## Task Execution Workflow
- Task prompts live in `docs/intro/llm_memory_vault_prompts/tasks/`.
- Execute tasks in order and validate acceptance criteria after each task.
- Update `tracking/checklist.md`, `tracking/cost_tracker.md`, and `tracking/daily_log.md` in the same folder.

## Coding Standards
- **Linting**: Run `poetry run ruff check .` before committing.
- **Formatting**: Auto-format with `poetry run black .`.
- **Type Checking**: Run `poetry run mypy vault/` for type validation.
- **Naming**: Use `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- **Pre-commit**: Run `poetry run pre-commit run --all-files` to validate all hooks.

## Testing Strategy
- **Unit Tests**: Required for all business logic.
- **Integration Tests**: Required for critical paths (ingestion, encryption, retrieval).
- **Coverage**: Aim for >80% coverage. Check with `poetry run pytest --cov=vault tests/`.
- **Run Tests**: `poetry run pytest tests/ -v`

## Commits
Follow Conventional Commits:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `chore:` for maintenance
- `refactor:` for code restructuring
- `test:` for test additions or changes
