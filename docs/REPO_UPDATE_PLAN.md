# Repository Update Plan: Project Memento -> LLM Memory Vault

This document outlines the plan to transform the current generic Node.js-based repository template into the specific **LLM Memory Vault** Python project structure, as defined in `docs/intro/PHASE1_DETAILED_PLAN_1.md`.

## 1. Cleanup & De-Node-ification
The current repository is initialized as a JavaScript project. We need to pivot to a Python-first structure.

*   [ ] **Remove/Archive JS Artifacts**:
    *   Delete `src/index.js` (generic entry point).
    *   Delete `package.json` (unless we decide to keep it for specific Node-based dev tools like `prettier` or `claude-code` management, but `poetry` handles Python deps). *Recommendation: Remove and use system/global `claude-code`, or keep minimal `package.json` only for strict dev-tool versioning if preferred.*
    *   Delete `tests/` if it contains JS tests (jest).

## 2. Python Architecture Implementation (Task 1.1.1)
Implement the folder structure defined in the Phase 1 Plan.

*   [ ] **Create Core Package Structure**:
    *   `vault/` (Root package)
        *   `__init__.py`
        *   `config/`
        *   `ingestion/`
        *   `classification/`
        *   `sanitization/`
        *   `distillation/`
        *   `storage/`
        *   `retrieval/`
        *   `api/`
        *   `cli/`
        *   `security/`
    *   `tests/` (Python tests)
        *   `__init__.py`
        *   `fixtures/`

*   [ ] **Configuration Files**:
    *   Create `pyproject.toml` (Poetry configuration) with dependencies:
        *   `fastapi`, `typer`, `pydantic`, `cryptography`, `sqlalchemy`, `qdrant-client`, `presidio-analyzer`.
    *   Update `.gitignore` for Python:
        *   Add `__pycache__/`, `*.pyc`, `.venv/`, `.env`, `*.db`, `*.key`, `vault_data/`, `.pytest_cache/`.
    *   Update `.editorconfig`:
        *   Ensure Python specific rules (indent_size = 4).

## 3. Documentation Migration & Alignment
Update the root documentation files to reflect the "LLM Memory Vault" identity.

*   [ ] **README.md**:
    *   Replace generic template text with "LLM Memory Vault" overview.
    *   Include "Quick Start" from `docs/intro/QUICK_START.md` (or `GETTING_STARTED.md`).
    *   Link to detailed architecture docs.

*   [ ] **SECURITY.md**:
    *   Update with specific policies from `docs/intro/PHASE1_DETAILED_PLAN_1.md` (Data Classification, PII handling).
    *   Define the "Zero Trust" local-first policy.

*   [ ] **CONTRIBUTING.md**:
    *   Update to reflect the "Tiered LLM" workflow (using `claude-code`, `CARE`, `RISEN`).
    *   Define coding standards (Type hints, Pydantic models).

*   [ ] **ROADMAP.md**:
    *   Replace generic roadmap with the 6-Phase Plan from `PHASE1_DETAILED_PLAN_1.md`.

*   [ ] **CHANGELOG.md**:
    *   Initialize with "v0.1.0 - Project Initialization".

*   [ ] **Organize `docs/`**:
    *   Move/Rename files from `docs/intro/` to appropriate permanent locations:
        *   `docs/architecture/` (Plan, Design docs)
        *   `docs/guides/` (Getting Started, Quick Ref)
        *   `docs/references/` (Prompts, Configs)

## 4. GitHub Workflows (CI/CD)
Update `.github/workflows` to support Python.

*   [ ] **ci.yml**:
    *   Replace Node.js/Jest steps with Python setup.
    *   Install Poetry.
    *   Run `pytest`.
    *   Run linting (`ruff` or `black`).

## 5. Execution Strategy

We will execute this update in the following order:

1.  **Scaffolding (Day 1 - Task 1.1.1)**: This task effectively covers Item 2 (Python Architecture) and parts of Item 1 (Cleanup).
2.  **Doc Update (Immediate)**: We can immediately rewrite `README.md` and `ROADMAP.md` to align the project context.
3.  **Dependency Setup (Day 1 - Task 1.1.2)**: This covers the `pyproject.toml` creation.

## Next Step
Run the **Project Scaffolding** task (Task 1.1.1) to create the directory structure and initialize the Python environment.
