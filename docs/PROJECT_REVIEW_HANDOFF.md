# Project Review Handoff (for Claude)

## Purpose
This document captures a repository-wide review and concrete suggested resolutions so follow-on contributors (including Claude) can execute against a clear, prioritized remediation plan.

## Review Scope
- Product and delivery docs (`README.md`, `ROADMAP.md`, `SECURITY.md`, `CONTRIBUTING.md`)
- Core implemented runtime modules (`vault/security/*`, `vault/storage/*`, `vault/config/models.py`, `vault/cli/main.py`)
- Project hygiene checks (`pytest`, `ruff`, `mypy`, CLI invocation)

## Executive Summary
The repository has a strong architectural direction and meaningful foundational security/storage primitives already implemented (Argon2id/HKDF/Fernet/session token lifecycle/encrypted blob store). However, there is currently a notable execution gap between documented product capabilities and the implemented surface area. The top priorities are schema correctness, taxonomy alignment, documentation/CLI parity, and test coverage.

---

## Key Findings and Suggested Resolutions

### 1) CLI capability mismatch with README
**Finding**
- README quickstart documents `vault init`, `vault import`, `vault list`, `vault show`, and `vault stats`.
- Implemented CLI currently exposes only a `version` command behavior.

**Impact**
- New contributors/users will fail during onboarding and may lose trust in project status.

**Suggested resolution**
- **Option A (recommended):** Implement a thin vertical slice for `init` and `list` immediately, then expand.
- **Option B:** Temporarily reduce README command claims until commands are implemented.
- Add a simple acceptance test matrix in docs (`Command`, `Status`, `Expected output`) and keep it updated in each PR.

---

### 2) ORM schema bug in `PIIFinding.confidence`
**Finding**
- `confidence` is typed as `Mapped[float]`, but persisted via SQLAlchemy `Integer`.

**Impact**
- Precision loss and semantic mismatch for confidence values intended in range `[0.0, 1.0]`.

**Suggested resolution**
1. Change DB type to `Float` (or bounded `Numeric(3,2)` if strict precision required).
2. Add migration script and data backfill (if existing records) to preserve compatibility.
3. Add tests ensuring round-trip precision and range enforcement.

---

### 3) Security taxonomy inconsistency
**Finding**
- Security policy describes `PUBLIC/INTERNAL/SENSITIVE/SECRET`.
- ORM enum currently uses `PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED`.

**Impact**
- Policy ambiguity across classification, sanitization, and retention decisions.

**Suggested resolution**
- Define a canonical taxonomy in one source-of-truth module/document.
- Align ORM enum and policy docs to canonical values.
- Add a unit test validating all policy references map to enum values.

---

### 4) Placeholder-heavy module surface area
**Finding**
- Several package areas are currently placeholders/docstrings only (`api`, `ingestion`, `retrieval`, `classification`, `sanitization`, `distillation`).

**Impact**
- Broad architecture is present, but low runnable feature depth.

**Suggested resolution**
- Execute one vertical slice end-to-end before broadening modules:
  1. `vault init` (vault root + DB bootstrap + salt/session bootstrap)
  2. Minimal conversation ingest path (single provider)
  3. `vault list` over persisted metadata
- For each slice: require tests + docs update in same PR.

---

### 5) Test coverage gap
**Finding**
- `pytest` currently discovers no tests in the Python project state.

**Impact**
- Security-sensitive primitives are not protected against regressions.

**Suggested resolution (priority order)**
1. `vault/security/crypto.py`:
   - deterministic key derivation given same salt/passphrase
   - passphrase validation edge cases
2. `vault/security/session.py`:
   - token validation success/failure
   - expiry and tampered session file behavior
3. `vault/storage/blobs.py`:
   - encrypt/decrypt success
   - wrong key/corrupt blob failure
   - delete/exists behavior
4. Add CI gate requiring tests to run for any PR touching `vault/security` or `vault/storage`.

---

### 6) Lint debt (low effort, high signal)
**Finding**
- Ruff currently reports multiple unused imports in core modules.

**Impact**
- Avoidable CI noise and reduced code quality signal.

**Suggested resolution**
- Run `ruff --fix` and keep lint clean with CI required checks.
- Add pre-commit hook docs step to contributor flow to reduce repeated issues.

---

### 7) Potential stale archive artifact
**Finding**
- `archive/index.test.js` references `../src/index` not present in this Python-centric codebase.

**Impact**
- Contributor confusion and false assumptions about supported runtimes.

**Suggested resolution**
- Either remove stale JS artifact, or move it under clearly marked historical examples with rationale.

---

## Prioritized Action Plan

### P0 (next PR)
1. Fix `PIIFinding.confidence` type + migration.
2. Align security taxonomy across code/docs.
3. Add initial tests for crypto/session/blob modules.

### P1
4. Implement `vault init` and `vault list` (or update README to match actual state).
5. Resolve lint issues and enforce in CI.

### P2
6. Expand ingestion and retrieval vertical slice.
7. Clean/archive stale non-Python artifacts.

---

## Definition of Done for Follow-Up
A follow-up remediation effort should be considered complete when:
- CLI docs match implemented commands exactly.
- Core security/storage modules have robust test coverage.
- Security taxonomy is canonical and consistent in docs + code.
- Lint/type/test checks pass in CI by default.
