# AI Agent Rules for Project Memento

As an AI agent contributing to this project, you must adhere to the following rules:

## 1. Branching & Commits
- Always work on a separate branch.
- Use the prefix `ai/` followed by a descriptive name (e.g., `ai/setup-encryption-layer`).
- Follow Conventional Commits for all commit messages.
- Note AI usage in Pull Request descriptions.

## 2. Documentation
- Keep playbooks in `docs/playbooks/` up to date.
- Document new features in the `README.md` or dedicated docs.
- Use Python docstrings (Google style) for modules, functions, and classes.

## 3. Testing & Quality
- Never submit a PR without tests.
- Run all quality checks before considering a task complete:
  - `poetry run pytest tests/ -v`
  - `poetry run ruff check .`
  - `poetry run black --check .`
  - `poetry run mypy vault/`
- Maintain at least 80% test coverage for new code.

## 4. Interaction
- Be proactive but avoid making destructive changes without confirmation.
- If a task is ambiguous, ask for clarification.
- Use the provided workflows in `.agent/workflows/` for common tasks.
