# Claude Handoff: Bug & Plan-Alignment Audit

Date: 2026-02-21
Repository: `ProjectMemento`

## Scope reviewed
- Core implementation under `vault/` (CLI, storage models, security/session, crypto).
- Delivery and planning docs (`README.md`, `ROADMAP.md`, `docs/intro/PHASE1_DETAILED_PLAN_1.md`, `docs/SESSION_SUMMARY_2026-02-17.md`).
- CI execution expectations (`.github/workflows/ci.yml`).

---

## High-priority issues (likely to cause incorrect behavior)

1. **PII confidence is typed as float but persisted as Integer**
   - `PIIFinding.confidence` is declared as `Mapped[float]` but mapped to `Integer`, while the comment expects a `0.0..1.0` range.
   - Risk: confidence values are truncated/incorrect in DB and downstream detection quality metrics are wrong.
   - Source: `vault/storage/models.py` (`confidence: Mapped[float] = mapped_column(Integer, nullable=False)`).

2. **`verify_passphrase()` is semantically incorrect and can produce false positives**
   - Docstring claims passphrase verification should check decryptability of a known marker, but implementation only checks that derivation runs without exception.
   - Because Argon2 derivation succeeds for almost any passphrase meeting length constraints, this can return `True` for an incorrect passphrase.
   - Risk: authentication logic built on this method will be insecure.
   - Source: `vault/security/crypto.py`.

3. **`SessionManager.create_session()` may fail when vault root directory does not yet exist**
   - Writes `.session` directly without ensuring parent directory exists.
   - Risk: `FileNotFoundError` during first-run flows where `vault_root` has not been created.
   - Source: `vault/security/session.py`.

---

## Medium-priority implementation issues

4. **Over-broad exception handling in token validation**
   - `validate_token()` catches `(KeyError, InvalidToken, Exception)` which swallows all runtime errors.
   - Risk: hides programming defects and complicates incident debugging/security triage.
   - Source: `vault/security/session.py`.

5. **`domain_tags` type/comment mismatch can cause schema drift**
   - `domain_tags` typed as `Optional[dict]` but inline comment says “List of tags or taxonomy.”
   - Risk: inconsistent payload shape across ingestion/classification code.
   - Source: `vault/storage/models.py`.

---

## Plan/documentation alignment gaps

6. **README advertises CLI commands that are not implemented**
   - README quick start shows `vault init/import/list/show/stats` usage.
   - Actual CLI currently only defines `version` command.
   - Impact: onboarding friction and broken first-run user experience.
   - Sources: `README.md`, `vault/cli/main.py`.

7. **Roadmap checklist is stale vs current repository state**
   - `ROADMAP.md` still marks dependencies/config/models/security/blob/session work as incomplete.
   - Repository already includes `pyproject.toml`, config models, SQLAlchemy models, crypto/session/blob modules.
   - Impact: planning noise, hard to know real execution status.
   - Sources: `ROADMAP.md`, `pyproject.toml`, `vault/config/models.py`, `vault/storage/models.py`, `vault/security/crypto.py`, `vault/security/session.py`, `vault/storage/blobs.py`.

8. **Session summary claims legacy JS removal, but archive still carries Node/Jest test artifact**
   - Session summary says legacy JS files were removed.
   - `archive/index.test.js` still references `../src/index` and Jest.
   - Impact: potential confusion for contributors and cleanup automation.
   - Sources: `docs/SESSION_SUMMARY_2026-02-17.md`, `archive/index.test.js`.

9. **CI test target expects tests directory that does not exist**
   - Workflow runs `pytest tests/ -v`.
   - Repository has no `tests/` directory currently.
   - Impact: CI fails with “no tests ran” / exit-code mismatch depending on pytest behavior.
   - Source: `.github/workflows/ci.yml`.

---

## Phase 1 plan alignment assessment

Reference expectations are from `docs/intro/PHASE1_DETAILED_PLAN_1.md` Milestones 1.1–1.4.

- **Milestone 1.1 (Scaffolding):** *Partially aligned*
  - Good: package skeleton and Poetry config exist.
  - Gap: test scaffold (`tests/`) missing while workflow expects it.

- **Milestone 1.2 (Core infra):** *Partially aligned*
  - Good: ORM models, key derivation, blob storage, session module exist.
  - Gaps: data-model bug (`confidence` type), fragile session-file creation path.

- **Milestone 1.3 (ChatGPT ingestion):** *Not aligned yet*
  - Adapter/import pipeline/dedup flow not yet present in runnable CLI workflows.

- **Milestone 1.4 (CLI retrieval):** *Not aligned yet*
  - `init/list/show/stats` commands are not implemented despite docs claiming usage.

---

## Suggested fix order for Claude

1. **Correct security/data correctness bugs first**
   - Fix `PIIFinding.confidence` column type.
   - Rework `verify_passphrase()` to perform real verification against a stored marker/checksum.
   - Ensure `SessionManager.create_session()` creates parent dirs.

2. **Stabilize reliability/diagnostics**
   - Narrow `validate_token()` exception handling to explicit expected failures.

3. **Restore truthfulness between docs and code**
   - Either implement missing CLI commands (`init/import/list/show/stats`) or temporarily reduce README claims.
   - Update `ROADMAP.md` checkboxes to match actual implementation status.

4. **Fix CI baseline**
   - Add minimal `tests/` scaffold and smoke tests, or change CI command to a command that remains meaningful with empty test tree.

5. **Clean residual legacy confusion**
   - Clarify `archive/` intent in docs, or remove stale JS artifacts if no longer needed.

---

## Validation commands executed during this audit

- `pytest -q` (result: no tests ran)
- `python -m compileall vault` (result: success)

