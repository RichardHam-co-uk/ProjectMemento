# ProjectMemento — Sonnet-Tier Task List (Phase 2)

> **Model:** Claude Sonnet 4.5 (Tier 3 in the project's allocation scheme)
> **Generated:** 2026-02-20
> **Source:** `docs/intro/PHASE2_DETAILED_PLAN.md`

Sonnet (Tier 3) handles all security-critical code, ML integrations,
redaction logic, and integration test design — where Haiku/GPT-4o-mini
would struggle with nuance but Opus would be over-budget.

---

## Why Sonnet for These Tasks?

| Criteria | Tier 1 (Local) | Tier 2 (Haiku) | **Tier 3 (Sonnet)** | Tier 4 (Opus) |
|----------|---------------|----------------|---------------------|----------------|
| Boilerplate/config | ✅ | ✅ | ✅ | ✅ |
| Well-defined wiring | ✅ | ✅ | ✅ | ✅ |
| Security-critical crypto | ❌ | ❌ | **✅** | ✅ |
| PII detection integration | ❌ | ❌ | **✅** | ✅ |
| Complex state management | ❌ | ❌ | **✅** | ✅ |
| Architecture review | ❌ | ❌ | ❌ | ✅ |
| Cost | $0 | ~$0.15/1M | **~$3/1M** | ~$15/1M |

---

## Task List

### Task 2.1.1 — Integration Test Suite
**Priority:** High (blocks Phase 2 confidence)
**Estimated hours:** 3
**Deliverable:** `tests/test_integration.py`
**Dependencies:** All Phase 1 tasks complete ✅

**What Sonnet must implement (5 test scenarios):**

1. `test_full_workflow_init_import_list_show()` — full happy path
2. `test_deduplication_on_reimport()` — second import returns `imported=0, skipped=2`
3. `test_partial_import_continues_on_error()` — malformed conversation → `failed=1`, DB has 1 row
4. `test_wrong_passphrase_fails_decryption()` — wrong key raises `ValueError`
5. `test_session_roundtrip()` — create → validate → expire (mocked datetime) → None

**Rules from Phase 1 lessons (must follow):**
- Every fixture conversation must have a unique `id` field
- Verify `len({c.external_id for c in parsed}) == len(parsed)`
- Generate test IDs as `str(uuid.uuid4())`, never padded integers
- Use `tmp_path` fixture; no shared state between tests
- Tag all tests `@pytest.mark.integration`
- No interactive prompts; CI-compatible

**Acceptance criteria:**
- [ ] All 5 scenarios pass
- [ ] Suite completes in <30 seconds
- [ ] No shared state between tests

---

### Task 2.3.2 — Presidio Pattern Detector
**Priority:** Critical (blocks 2.3.4, 2.4.2)
**Estimated hours:** 4
**Deliverable:** `vault/sanitization/presidio_detector.py`
**Dependencies:** Task 2.3.1 (PIIDetector base interface — Tier 2)

**What Sonnet must implement:**

```python
class PresidioDetector(BasePIIDetector):
    def detect(self, text: str) -> List[PIISpan]: ...
    def detector_name(self) -> str: ...
```

**Presidio entity types to configure:**
`EMAIL_ADDRESS`, `PHONE_NUMBER`, `CREDIT_CARD`, `CRYPTO`, `IP_ADDRESS`,
`IBAN_CODE`, `US_SSN`, `UK_NHS`, `PERSON`, `URL`, `LOCATION`, `DATE_TIME`

**Custom recognisers to add:**
- OpenAI API key: `sk-[A-Za-z0-9]{48}`
- Anthropic API key: `sk-ant-[A-Za-z0-9-]{90+}`
- Bearer tokens: `Bearer [A-Za-z0-9._-]{20,}`
- UK phone: `+44` and `07xxx` formats

**Implementation constraints:**
- Lazy-load `AnalyzerEngine` (singleton on first call — expensive init)
- Default confidence threshold: `0.7`; validate `0 < t < 1`
- Never log matched text — log only: type, offsets, confidence
- Handle `ImportError` if presidio not installed (clear error message)
- Performance target: <200ms per typical conversation

**Acceptance criteria:**
- [ ] All standard + custom PII types detected
- [ ] Returns empty list for lorem ipsum (no false positives)
- [ ] Lazy init working (first call slow, subsequent calls fast)
- [ ] `ImportError` handled cleanly

---

### Task 2.3.3 — LLM Guard NER Detector
**Priority:** High (can run in parallel with 2.3.2)
**Estimated hours:** 3
**Deliverable:** `vault/sanitization/llmguard_detector.py`
**Dependencies:** Task 2.3.1

**What Sonnet must implement:**

```python
class LLMGuardDetector(BasePIIDetector):
    def detect(self, text: str) -> List[PIISpan]: ...
    def detector_name(self) -> str: ...
```

**Target NER entity types:** `PERSON`, `ORG`, `GPE` (location), `DATE`

**Strategy:**
1. Try `llm_guard.input_scanners.Anonymize` first
2. Fallback: `transformers` NER pipeline (`dslim/bert-base-NER`)
3. Graceful degradation: if neither available, return empty list + `WARNING` log

**Model caching:** `~/.cache/vault/models/` — show progress bar on first download

**Minimum confidence threshold:** `0.85` (NER has lower precision than pattern matching)

**Constraints:**
- Runs fully offline after initial model download
- No API calls ever
- Never log entity text

**Acceptance criteria:**
- [ ] "John Smith" detected as PERSON
- [ ] "Anthropic" detected as ORG
- [ ] "London" detected as GPE
- [ ] Graceful fallback if deps missing (no crash, just WARNING)
- [ ] Fully offline after first run

---

### Task 2.3.4 — Combined PII Detector
**Priority:** High (blocks 2.4.2, 2.4.3)
**Estimated hours:** 2
**Deliverable:** `vault/sanitization/detector.py`
**Dependencies:** Task 2.3.2 + Task 2.3.3

**What Sonnet must implement:**

```python
class CombinedPIIDetector:
    def __init__(
        self,
        use_presidio: bool = True,
        use_llm_guard: bool = True,
        min_confidence: float = 0.7,
    ): ...

    def detect(self, text: str) -> PIIDetectionResult: ...
    def detect_in_blob(self, blob_bytes: bytes, encoding: str = "utf-8") -> PIIDetectionResult: ...
```

**Deduplication/overlap rules (implement in `combine_spans()`):**
- Two overlapping spans → keep the one with higher confidence
- Same span from both detectors → merge (keep Presidio confidence)
- Output sorted by `start` offset

**Config surface:**
- `min_confidence` per detector
- `ignored_types: list[str]` allowlist
- `detector_names()` method for audit logging

**Acceptance criteria:**
- [ ] Correctly merges spans from both detectors
- [ ] Overlap resolution produces deterministic output
- [ ] Empty result for clean text
- [ ] All constructor params respected

---

### Task 2.4.2 — Redaction Engine
**Priority:** Critical (security-critical, blocks 2.4.3 and 2.5.1)
**Estimated hours:** 4
**Deliverable:** `vault/sanitization/redactor.py`
**Dependencies:** Task 2.3.4 + Task 2.4.1 (Policy Engine — Tier 2)

**What Sonnet must implement:**

```python
@dataclass
class RedactionResult:
    conversation_id: str
    messages_processed: int
    pii_spans_found: int
    pii_spans_redacted: int
    pii_spans_masked: int
    pii_spans_flagged: int
    errors: List[str]

class RedactionEngine:
    def __init__(
        self,
        detector: CombinedPIIDetector,
        policy: PolicyEngine,
        blob_store: BlobStore,
        db: VaultDB,
    ): ...

    def redact_conversation(
        self,
        conversation_id: str,
        master_key: bytes,
    ) -> RedactionResult: ...

    def _apply_redaction(
        self,
        text: str,
        spans: List[PIISpan],
        actions: Dict[PIISpan, str],
    ) -> str: ...
```

**Redaction tokens:**
| Action | Token format |
|--------|-------------|
| `redact` | `[REDACTED:EMAIL_ADDRESS]` |
| `mask` | `[PERSON_1]`, `[PERSON_2]` (consistent within conversation) |
| `flag` | text unchanged — only PIIFinding record written |
| `allow` | text unchanged |

**Masking consistency:**
- Track `"John Smith" → [PERSON_1]` within one conversation
- Same name → same token within one conversation
- Reset mapping between conversations (no cross-conversation leakage)

**Atomic blob replacement:**
1. Write new redacted blob → `sanitized_blob_uuid`
2. Update DB: `message.sanitized_blob_uuid = new_blob_id`
3. Keep `message.content_blob_uuid` unchanged (original preserved)
4. If DB update fails → delete new blob (rollback)

**Safety rules:**
- Never log redacted content
- Validate span offsets before applying (prevent `IndexError`)
- Write `PIIFinding` record per span (DB audit trail)

**Acceptance criteria:**
- [ ] Email, phone, API keys redacted in blob content
- [ ] Masking is consistent within a conversation
- [ ] Original blob preserved (non-destructive)
- [ ] `PIIFinding` records written to DB
- [ ] `RedactionResult` counts accurate
- [ ] Atomic: no partial state on failure

---

### Task 2.4.3 — Wire PII into Import Pipeline
**Priority:** High
**Estimated hours:** 2
**Deliverable:** Update `vault/ingestion/pipeline.py`
**Dependencies:** Task 2.4.2 + Task 2.4.1

**What Sonnet must implement:**

Update `ImportPipeline.__init__()`:
```python
def __init__(
    self,
    db: VaultDB,
    blob_store: BlobStore,
    key_manager: KeyManager,
    detector: CombinedPIIDetector | None = None,
    policy: PolicyEngine | None = None,
):
```

In `_import_one()`, after storing blobs:
```python
if self.detector and self.policy and self.policy.should_auto_detect():
    redactor = RedactionEngine(self.detector, self.policy, self.blob_store, self.db)
    redactor.redact_conversation(conv_id, master_key)
```

Update CLI `import` command:
- Load `policies.yaml` from `vault_path` if it exists → pass detector+policy
- Add `--no-sanitize` flag to skip detection even if policy says `auto_detect_on_import: true`
- Show PII summary in import output (spans found, redacted)

**Acceptance criteria:**
- [ ] Auto-detection triggers on import when `auto_detect_on_import: true`
- [ ] `--no-sanitize` suppresses detection
- [ ] Import not more than 2× slower with detection enabled
- [ ] Import summary includes PII span counts

---

### Task 2.6.1 — Token Vault Implementation
**Priority:** High
**Estimated hours:** 4
**Deliverable:** `vault/security/token_vault.py`
**Dependencies:** Phase 1 crypto module (`KeyManager`)

**What Sonnet must implement:**

```python
class TokenVault:
    """
    Encrypted key-value store for LLM provider API credentials.

    Layout: vault_root/tokens/<name>.tok
    Format: Fernet-encrypted JSON → {"provider": str, "key": str, "created_at": str}
    """
    def __init__(self, vault_root: Path, key_manager: KeyManager): ...

    def store(self, name: str, provider: str, value: str, master_key: bytes) -> None: ...
    def retrieve(self, name: str, master_key: bytes) -> str | None: ...
    def delete(self, name: str) -> bool: ...
    def list_names(self) -> list[str]: ...
```

**Key derivation per credential:**
```
credential_key = HKDF(
    master_key,
    salt=name.encode("utf-8"),
    info=b"vault-token-credential",
    length=32,
)
```

**File rules:**
- Path: `vault_root/tokens/{name}.tok`
- Permissions: `0600` (set after write)
- Write pattern: write to `{name}.tok.tmp` → `os.rename()` (atomic)
- Secure delete: overwrite file content with zeros before `unlink()`

**Validation:**
- `name` must match `^[a-zA-Z0-9-]+$` (alphanumeric + hyphens only)
- `value` must not be empty
- Wrong master key → `ValueError` on retrieve

**Safety rules:**
- Never log credential values
- `list_names()` returns only file stems, never values

**Acceptance criteria:**
- [ ] Store + retrieve with correct key works
- [ ] Retrieve with wrong key raises `ValueError`
- [ ] Delete overwrites then unlinks
- [ ] `list_names()` exposes no values
- [ ] File permissions `0600` on all `.tok` files
- [ ] Atomic write (tmp → rename)

---

## Execution Order for Sonnet

```
Day 11:  Task 2.1.1 — Integration Tests          (3h, standalone)
Day 13:  Task 2.3.2 — Presidio Detector           (4h)
         Task 2.3.3 — LLM Guard Detector           (3h, parallel with 2.3.2)
Day 14:  Task 2.3.4 — Combined Detector           (2h, needs 2.3.2 + 2.3.3)
Day 16:  Task 2.4.2 — Redaction Engine            (4h, needs 2.4.1 from Tier 2)
Day 17:  Task 2.4.3 — Wire PII into Pipeline      (2h, needs 2.4.2)
Day 18:  Task 2.6.1 — Token Vault                 (4h, standalone)
```

**Total: 7 tasks · 22 estimated hours**

---

## Not for Sonnet

These are explicitly allocated to other tiers:

| Task | Tier | Reason |
|------|------|--------|
| 2.2.1 Audit logger | Tier 2 (Haiku) | Pattern is clear, no novel logic |
| 2.3.1 PII base interface | Tier 2 (Haiku) | Pure dataclass/ABC scaffolding |
| 2.3.5 PII unit tests | Tier 2 (Haiku) | Test generation from defined spec |
| 2.4.1 Policy engine | Tier 2 (Haiku) | YAML + Pydantic wiring |
| 2.5.1 `vault sanitize` CLI | Tier 2 (Haiku) | CLI wiring from spec |
| 2.5.2 `vault show` sanitized | Tier 2 (Haiku) | Small CLI update |
| 2.6.2 Token vault CLI | Tier 1 (Local) | Boilerplate CLI scaffolding |
| 2.7.1 `vault policy` CLI | Tier 1 (Local) | Boilerplate CLI scaffolding |
| 2.7.2 Default policy in init | Tier 1 (Local) | One-liner file write |
| 2.8.1 Sanitization unit tests | Tier 2 (Haiku) | Test generation from spec |
| 2.8.2 Security review | Tier 4 (Opus) | Architecture-level reasoning |

---

*Source of truth: `docs/intro/PHASE2_DETAILED_PLAN.md`*
*Phase 2 estimated completion: 2026-03-04*
