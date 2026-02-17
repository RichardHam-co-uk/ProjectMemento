# Repo Update Plan (Project Memento)

## Purpose
Align the repository templates and docs with the Project Memento / LLM Memory Vault vision defined in docs/intro, then prepare the repo for Phase 1 execution.

## What I Read
- Core intro docs: README, GETTING_STARTED, QUICK_REFERENCE, DELIVERY_SUMMARY, PHASE1_DETAILED_PLAN_1
- Strategy notes: PROJECT 1 - AI Local Memory Bank
- Execution package: llm_memory_vault_prompts (docs, tasks, reference, tracking)

## Guiding Principles
- Local-first, encrypted storage with clear separation of metadata and content blobs.
- Phase 1 is CLI-first (init, import, list, show, stats) with ChatGPT import.
- Security-critical components are explicit and reviewed (key derivation, blob storage, session tokens).
- Documentation is aligned to the Phase 1 plan and task prompts.

## Primary Gaps in the Current Repo
- Top-level README, ROADMAP, and playbooks are generic templates vs project-specific.
- The repo structure is JS-based (src/index.js, tests/index.test.js), but Phase 1 plan is Python/Poetry and vault/ package.
- Intro package includes two levels of duplicated prompt folders; needs a decision on canonical location.
- Tasks, trackers, and reference files are isolated under docs/intro and not surfaced in top-level documentation.

## Update Strategy
Phase 0: Decide the canonical source of truth for prompts and trackers.
- Recommend: docs/intro/llm_memory_vault_prompts as canonical.
- De-emphasize nested llm_memory_vault_prompts/llm_memory_vault_prompts copy unless needed for archival.

Phase 1: Documentation alignment (no code changes).
- Update top-level README to describe Project Memento and link to intro docs.
- Update ROADMAP to the Phase 1 through Phase 3 milestones.
- Update docs/playbooks to match the intro architecture and workflow.
- Update CONTRIBUTING and SECURITY to reflect local-first and sensitive data handling.

Phase 2: Repo structure alignment (code and config).
- Introduce Python package scaffold per Phase 1 plan (vault/ and tests/).
- Add Poetry pyproject.toml (per task 1.1.2).
- Add .pre-commit-config.yaml aligned to plan.
- Retain existing JS files only if they are intentionally part of Phase 1. Otherwise move to a legacy/ or archive/ folder.

Phase 3: Execution readiness.
- Ensure task prompts are referenced from top-level docs.
- Add a short "How to run Phase 1" checklist to the repo root.
- Confirm tracking files location and usage.

## Proposed Update Order
1. Documentation alignment (README, ROADMAP, docs/playbooks).
2. Decide canonical prompt location and remove or annotate duplicates.
3. Add Python scaffold and pyproject.toml (Task 1.1.1 and 1.1.2).
4. Add config models, pre-commit hooks (Task 1.1.3 and 1.1.4).
5. Prepare CLI skeleton and initial storage scaffolding (Tasks 1.2.x and 1.3.x).

## Open Decisions to Confirm
- Canonical prompt location: keep only one copy or keep duplicates with a clear note.
- Whether to keep current JS src/tests or archive them.
- Naming: keep "Project Memento" or rename repo to "LLM Memory Vault".
- Whether to expose Phase 2+ roadmap now or keep it lightweight.

## Risks and Mitigations
- Risk: Conflicting instructions between intro docs and template docs.
  - Mitigation: Treat docs/intro as source of truth; annotate differences.
- Risk: Overwriting user changes.
  - Mitigation: Only update specified files; do not delete without explicit approval.

## Deliverables for the Update
- Updated top-level README with project summary, scope, and links.
- Updated ROADMAP and playbooks aligned to Phase 1.
- Canonical prompt directory with clear usage notes.
- Phase 1 scaffold ready for task execution.

## Success Criteria
- Repo docs clearly describe Phase 1 and how to execute it.
- No ambiguity about where prompts and trackers live.
- Codebase matches the Phase 1 plan structure.
