# LLM Memory Vault - Phase 2 Detailed Implementation Plan

## Phase 2 Overview: Security & Sanitisation

**Duration:** 2 weeks (10 working days)
**Goal:** PII detection and redaction pipeline, audit logging, policy engine, and token vault
**Team:** Tiered LLM allocation based on task complexity
**Final Deliverable:** >99% PII detection on test corpus; all vault operations fully audited; credential vault operational

**Phase 1 Status:** ✅ Complete (2026-02-18)
**Phase 2 Start:** Day 11

---

## Lessons Learned from Phase 1 (Apply to All Future Phases)

These issues were discovered during Phase 1 implementation and testing. Every
agent picking up a task in Phase 2+ must read this section before starting.

### 1. Test Fixture Data Must Have Unique External IDs
**What happened:** Two conversations in `sample_chatgpt_export.json` lacked a
top-level `id` field. The ChatGPT adapter fell back to `external_id=""` for
both, causing `_stable_uuid("chatgpt", "")` to produce the same UUID5 for both
conversations → UNIQUE constraint violation in SQLite.

**Rule:** Every test fixture conversation **must** include a unique `id` field.
Verify with: `assert len({c.external_id for c in parsed}) == len(parsed)`

---

### 2. Always Verify API Signatures Before Wiring
**What happened:** `BlobStore.retrieve(blob_id, master_key, conv_id)` — the
argument order is `(blob_id, master_key, conversation_id)`. The CLI initially
called it as `retrieve(blob_id, conv_id, master_key)` (swapped last two args),
which caused silent wrong-key decryption failures.

**Rule:** Before calling any method from another module, read its actual
signature. Never assume argument order matches usage order.

---

### 3. Callback Signatures Must Match Exactly
**What happened:** The CLI passed a `(imported, skipped, failed)` 3-arg
callback to `ImportPipeline.import_conversations()`, but the pipeline calls
`callback(current, total)` — 2 args. This caused a `TypeError` at runtime.

**Rule:** Check `Callable` type hints in the target function signature before
implementing callbacks. Write a stub test: `cb = lambda *a: None` → verify arg
count.

---

### 4. ORM Dataclass Attribute Names ≠ Python Field Names
**What happened:** Tests referenced `ParsedConversation.hash` — but the actual
attribute is `ParsedConversation.content_hash` (set by the adapter).

**Rule:** Read the dataclass definition in `base.py` before referencing fields
in tests. Do not assume names match the ORM model.

---

### 5. Test ID Generation Must Produce Actually Unique Values
**What happened:** `f"msg-{idx:036d}"[:36]` for idx=1,2,3 produced identical
strings because the format pads with leading zeros and the truncation at 36
chars cut off the distinguishing digit.

**Rule:** When generating test IDs: use `str(uuid.uuid4())` or construct the
format string so truncation cannot collapse distinct values. Prefer:
```python
msg_id = f"{idx:08d}-{idx:04d}-{idx:04d}-{idx:04d}-{idx:012d}"
```

---

### 6. The ChatGPT Adapter Rejects Empty Arrays
**What happened:** `validate_format("[]")` returns `False` — the adapter
requires at least one element with a `mapping` key. A test assumed empty
arrays were valid.

**Rule:** Read `validate_format()` docstring carefully. Empty is not always
valid. Add a test that confirms the documented contract.

---

### 7. `del variable` for Sensitive Data Is Best-Effort Only
**What happened:** No bug, but a note — `del passphrase` in CPython only
removes the reference; the string object may remain in memory until GC.

**Rule:** Use `del` for sensitive values as a best-effort hygiene measure.
Document this limitation in security-critical code. Never rely on `del` as a
security guarantee.

---

### 8. Always Run `python -m py_compile` Before Committing
**Rule:** Run `python -m py_compile vault/path/to/module.py && echo OK` on
any edited file before committing. Catches syntax errors before CI.

---

---

## Team Structure & Capabilities

### Tier 1: Local LLMs (Llama3b, DeepSeek-Coder, Qwen)
**Use for:**
- Boilerplate YAML/config file generation
- Simple CLI command scaffolding
- Template population from examples
- Basic list/get/set operations

**Avoid for:** Security logic, NLP pipelines, policy enforcement

**Cost:** $0

---

### Tier 2: Budget Cloud (GPT-4o-mini, Claude Haiku 4.5)
**Use for:**
- Test case generation for well-defined modules
- Documentation writing
- Error handling and validation wiring
- Audit log write-path implementation (pattern is clear)
- Config model expansion (Pydantic)
- `vault sanitize` and `vault policy` CLI command wiring

**Cost:** ~$0.15 / 1M in · ~$0.60 / 1M out

---

### Tier 3: Advanced (Claude Sonnet 4.5, GPT-4o)
**Use for:**
- All security-critical code (PII detection, redaction, token vault)
- Presidio + LLM Guard integration
- Redaction engine (span-level blob rewriting)
- Integration test suite design and implementation
- Policy engine architecture and rule evaluation
- Wiring PII detection into import pipeline

**Cost:** ~$3 / 1M in · ~$15 / 1M out

---

### Tier 4: Expert (Claude Opus 4.5, Perplexity)
**Use for:**
- Security architecture review of the full Phase 2 system
- Research on PII detection recall benchmarks
- Performance review of Presidio config

**Cost:** ~$15 / 1M in · ~$75 / 1M out
**Budget:** Reserve for final security review only (1 use)

---

## Milestone Breakdown

### 🎯 Milestone 2.1: Integration Tests & Audit Logging (Days 11–12)
**Objective:** Close out Phase 1 properly with end-to-end tests; wire audit trail
**Success Criteria:**
- ✅ Full workflow tested: `init → import → list → show → stats`
- ✅ Session expiry and re-auth tested
- ✅ Deduplication workflow tested
- ✅ AuditEvent written for every vault read/write
- ✅ `vault audit` command shows recent events

---

### 🎯 Milestone 2.2: PII Detection Engine (Days 13–15)
**Objective:** Two-stage PII detector (pattern + NER) with high recall
**Success Criteria:**
- ✅ Presidio pattern detector live (email, phone, SSN, API keys, IPs, credit cards)
- ✅ LLM Guard NER detector live (person names, orgs, locations)
- ✅ Combined detector returns ranked, deduplicated spans
- ✅ Detection runs on any `bytes` payload (decrypted blob content)
- ✅ >99% recall on test corpus fixture
- ✅ Unit tests covering all PII types

---

### 🎯 Milestone 2.3: Policy Engine & Redaction (Days 16–17)
**Objective:** YAML-driven policy rules + in-place redaction of blobs
**Success Criteria:**
- ✅ `policies.yaml` schema defined with per-sensitivity-level rules
- ✅ Policy engine loads and evaluates rules against detected PII
- ✅ Redaction engine rewrites blob content with `[REDACTED:TYPE]` tokens
- ✅ Re-encrypted blobs stored atomically (old blob overwritten securely)
- ✅ PII detection auto-triggered on import (optional, policy-controlled)
- ✅ `vault sanitize <id>` CLI command works

---

### 🎯 Milestone 2.4: Token Vault & CLI Polish (Days 18–20)
**Objective:** Secure credential storage; full CLI integration
**Success Criteria:**
- ✅ Token vault encrypts API keys (OpenAI, Anthropic, Perplexity) with master key
- ✅ `vault token set <provider> <key>` stores securely
- ✅ `vault token get <provider>` retrieves and prints (with confirmation)
- ✅ `vault policy` command lists/sets active policies
- ✅ All Phase 2 unit tests passing (>80% coverage on new modules)
- ✅ Tier 4 security review completed

---

## Detailed Task Breakdown

---

## DAY 11: Integration Tests (Phase 1 Close-out)

### Task 2.1.1: Integration Test Suite
**Assigned to:** Tier 3 (Claude Sonnet 4.5)
**Estimated Time:** 3 hours
**Dependencies:** All Phase 1 tasks complete
**Deliverable:** `tests/test_integration.py`

**RISEN Prompt:**
```
Role: QA engineer writing end-to-end integration tests
Context: Phase 1 of LLM Memory Vault is complete. Need full workflow tests.

Instructions:
1. Create tests/test_integration.py with pytest fixtures:
   - tmp vault_root
   - real KeyManager + VaultDB + BlobStore + ImportPipeline
   - sample_chatgpt_export.json fixture

2. Test scenarios (each is a separate test function):

   test_full_workflow_init_import_list_show():
     - Init vault (derive key, create schema)
     - Import sample fixture (2 conversations)
     - Assert list returns 2 items
     - Assert show decrypts content correctly
     - Assert stats returns correct counts

   test_deduplication_on_reimport():
     - Import same file twice
     - Assert second import: imported=0, skipped=2

   test_partial_import_continues_on_error():
     - Import file with one valid + one malformed conversation
     - Assert imported=1, failed=1
     - Assert DB has 1 conversation

   test_wrong_passphrase_fails_decryption():
     - Init vault with passphrase A
     - Derive key with passphrase B
     - Assert blob retrieve raises ValueError

   test_session_roundtrip():
     - Create session from master key
     - Validate token → returns same master key
     - Wait for expiry (mock datetime)
     - Assert validate returns None after expiry

3. Use pytest.mark.integration tag
4. All tests must clean up after themselves (tmp_path)

Safety:
- Never write real passphrases to disk
- Verify blobs cleaned up in teardown
```

**Acceptance Criteria:**
- [ ] All 5 integration scenarios pass
- [ ] Tests run in <30 seconds total
- [ ] No shared state between tests
- [ ] CI-compatible (no interactive prompts)

---

## DAY 12: Audit Logging

### Task 2.2.1: Audit Log Write Path
**Assigned to:** Tier 2 (Claude Haiku 4.5)
**Estimated Time:** 2 hours
**Dependencies:** Task 2.1.1 (AuditEvent model already in ORM)
**Deliverable:** `vault/security/audit.py` + updates to pipeline and CLI

**CARE Prompt:**
```
Context: AuditEvent ORM model exists in vault/storage/models.py.
         Need to wire audit writes into all vault operations.
Action: Create vault/security/audit.py with AuditLogger class
Result: All reads/writes/deletes recorded to audit_events table
Example: See AuditEvent model for field names

Implement:
1. AuditLogger class:
   class AuditLogger:
       def __init__(self, db: VaultDB):
           self.db = db

       def log(
           self,
           actor: str,           # "cli", "api", "pipeline"
           action: str,          # "import", "read", "delete", "search", "init"
           resource_type: str,   # "conversation", "blob", "key", "session"
           resource_id: str | None = None,
           details: dict | None = None,
           success: bool = True,
       ) -> None:
           """Write one AuditEvent row. Swallows errors (audit must never crash the app)."""

2. Wire into ImportPipeline._import_one():
   - log action="import", resource_type="conversation" on success
   - log action="import", success=False on failure

3. Wire into CLI show command:
   - log action="read", resource_type="conversation" on each decrypt

4. Wire into vault init:
   - log action="init", resource_type="key"

5. Add vault audit CLI command:
   @app.command()
   def audit(limit: int = 20):
       """Show recent vault audit events."""
       # Rich table: timestamp | actor | action | resource | success
```

**Acceptance Criteria:**
- [ ] AuditLogger class created
- [ ] Swallows all errors (never crashes main flow)
- [ ] `vault audit` shows last N events in a table
- [ ] Import pipeline writes audit entries
- [ ] Session events logged (create, validate, clear)

---

## DAY 13–14: PII Detection Engine

### Task 2.3.1: PIIDetector Base Interface
**Assigned to:** Tier 2 (GPT-4o-mini)
**Estimated Time:** 1 hour
**Dependencies:** None
**Deliverable:** `vault/sanitization/base.py`

**RISEN Prompt:**
```
Role: Interface architect
Context: Need a standard interface for PII detectors (pattern-based + NER)

Instructions:
1. Define PIISpan dataclass:
   @dataclass
   class PIISpan:
       pii_type: str          # "EMAIL", "PHONE", "PERSON", etc.
       start: int             # character offset in text
       end: int               # character offset (exclusive)
       text: str              # matched text (for logging only — never stored)
       confidence: float      # 0.0 to 1.0
       detector: str          # "presidio" or "llm_guard"

2. Define BasePIIDetector ABC:
   class BasePIIDetector(ABC):
       @abstractmethod
       def detect(self, text: str) -> List[PIISpan]:
           """Return all PII spans found in text."""

       @abstractmethod
       def detector_name(self) -> str:
           """Identifier for this detector."""

3. Define PIIDetectionResult dataclass:
   @dataclass
   class PIIDetectionResult:
       spans: List[PIISpan]
       text_length: int
       detector_names: List[str]

       @property
       def has_pii(self) -> bool:
           return len(self.spans) > 0

4. Define combine_spans() utility:
   def combine_spans(spans_a, spans_b) -> List[PIISpan]:
       """Merge two span lists, resolve overlaps (keep highest confidence)."""

Next: Presidio and LLM Guard detectors implement this interface
```

**Acceptance Criteria:**
- [ ] PIISpan dataclass defined
- [ ] BasePIIDetector ABC defined
- [ ] PIIDetectionResult defined
- [ ] combine_spans() handles overlapping spans correctly
- [ ] Type hints complete

---

### Task 2.3.2: Presidio Pattern Detector
**Assigned to:** Tier 3 (Claude Sonnet 4.5) — Security Critical
**Estimated Time:** 4 hours
**Dependencies:** Task 2.3.1
**Deliverable:** `vault/sanitization/presidio_detector.py`

**RISEN Prompt:**
```
Role: Security engineer, expert in PII detection and Presidio
Context: Need pattern-based PII detection using Microsoft Presidio

Instructions:
1. Implement PresidioDetector(BasePIIDetector):
   - Use presidio_analyzer.AnalyzerEngine
   - Configure recognisers for:
       EMAIL_ADDRESS, PHONE_NUMBER, CREDIT_CARD,
       CRYPTO (API keys / wallet addresses),
       IP_ADDRESS, IBAN_CODE, US_SSN, UK_NHS,
       PERSON (via spaCy NLP engine),
       URL, LOCATION, DATE_TIME
   - Map Presidio entity types → vault PIIType enum values

2. Custom recognisers (add to engine):
   a. API key pattern recogniser:
      - Matches: sk-[A-Za-z0-9]{48} (OpenAI)
      - Matches: sk-ant-[A-Za-z0-9-]{90+} (Anthropic)
      - Matches: Bearer [A-Za-z0-9._-]{20,}
      - Matches: [A-Za-z0-9]{32,64} (generic API keys, high entropy only)
   b. UK phone recogniser:
      - Matches +44 and 07xxx formats

3. detect(text: str) -> List[PIISpan]:
   - Run AnalyzerEngine.analyze(text, language="en")
   - Convert RecognizerResult objects to PIISpan
   - Filter results below confidence_threshold (default 0.7)
   - Return deduplicated, sorted spans

4. Lazy-load the engine (expensive to init):
   - Use module-level singleton pattern
   - Init on first call to detect()

Safety:
- Never log the matched text content
- Only log: type, span offsets, confidence
- Validate confidence threshold (0.0 < t < 1.0)
- Handle ImportError if presidio not installed (clear error)

Performance target: <200ms per conversation on typical hardware
```

**Acceptance Criteria:**
- [ ] All standard PII types detected
- [ ] Custom API key patterns detected
- [ ] Returns empty list for clean text (no false positives on lorem ipsum)
- [ ] Lazy initialisation working
- [ ] Performance <200ms per typical conversation

---

### Task 2.3.3: LLM Guard NER Detector
**Assigned to:** Tier 3 (Claude Sonnet 4.5) — Security Critical
**Estimated Time:** 3 hours
**Dependencies:** Task 2.3.1
**Deliverable:** `vault/sanitization/llmguard_detector.py`

**RISEN Prompt:**
```
Role: Security engineer, expert in NER-based PII detection
Context: Need NER-based PII detection to catch names, orgs, locations
         that Presidio pattern matching misses.

Instructions:
1. Implement LLMGuardDetector(BasePIIDetector):
   - Use llm_guard.input_scanners.Anonymize or BanSubstrings
   - OR use transformers NER pipeline (dslim/bert-base-NER or similar)
     as a fallback if llm_guard is not installed
   - Target entity types: PERSON, ORG, GPE (location), DATE

2. Implement detect(text: str) -> List[PIISpan]:
   - Run NER pipeline on text
   - Convert NER tags to PIISpan objects
   - Map entity labels to vault PIIType enum
   - Apply minimum confidence threshold (default 0.85 for NER — lower precision)

3. Handle model download gracefully:
   - First run downloads model (~400MB)
   - Cache in ~/.cache/vault/models/
   - Show progress bar during download

4. Fallback mode:
   - If llm_guard and transformers not available, return empty list
   - Log a WARNING "NER detector not available — install llm_guard"

Safety:
- Run NER locally only (no API calls)
- Never log entity text
- Model runs fully offline after initial download
```

**Acceptance Criteria:**
- [ ] Person names detected (e.g. "John Smith")
- [ ] Organisations detected (e.g. "Anthropic", "Google")
- [ ] Locations detected (e.g. "London", "123 Main Street")
- [ ] Graceful fallback if dependencies missing
- [ ] Works fully offline

---

### Task 2.3.4: Combined PII Detector
**Assigned to:** Tier 3 (Claude Sonnet 4.5)
**Estimated Time:** 2 hours
**Dependencies:** Task 2.3.2, Task 2.3.3
**Deliverable:** `vault/sanitization/detector.py`

**RISEN Prompt:**
```
Role: Integration engineer
Context: Combine Presidio and LLM Guard into one unified detector

Instructions:
1. Create CombinedPIIDetector:
   class CombinedPIIDetector:
       def __init__(
           self,
           use_presidio: bool = True,
           use_llm_guard: bool = True,
           min_confidence: float = 0.7,
       ):
           self._detectors: list[BasePIIDetector] = []

       def detect(self, text: str) -> PIIDetectionResult:
           """Run all enabled detectors, combine and deduplicate spans."""
           # 1. Run each detector
           # 2. combine_spans() to merge and resolve overlaps
           # 3. Filter by min_confidence
           # 4. Return PIIDetectionResult

       def detect_in_blob(
           self,
           blob_bytes: bytes,
           encoding: str = "utf-8"
       ) -> PIIDetectionResult:
           """Convenience: decode bytes and detect."""

2. Deduplication logic in combine_spans():
   - If two spans overlap, keep the one with higher confidence
   - If same span found by both detectors, merge (keep presidio confidence)
   - Sort output by start offset

3. Configuration:
   - Accept min_confidence per detector
   - Accept list of PII types to ignore (allowlist)
   - Expose detector_names() for audit logging

Example usage:
```python
detector = CombinedPIIDetector(use_presidio=True, use_llm_guard=True)
result = detector.detect_in_blob(blob_content)

if result.has_pii:
    for span in result.spans:
        print(f"{span.pii_type} at [{span.start}:{span.end}] ({span.confidence:.2f})")
```
```

**Acceptance Criteria:**
- [ ] Correctly combines spans from both detectors
- [ ] Overlap resolution working
- [ ] Returns empty result for clean text
- [ ] Configurable via constructor

---

### Task 2.3.5: PII Detection Unit Tests
**Assigned to:** Tier 2 (GPT-4o-mini)
**Estimated Time:** 2 hours
**Dependencies:** Task 2.3.4
**Deliverable:** `tests/test_pii_detection.py`

**CARE Prompt:**
```
Context: CombinedPIIDetector wraps Presidio and LLM Guard
Action: Write pytest unit tests for the detection pipeline
Result: >80% coverage on vault/sanitization/

Test cases needed:
- test_detect_email_address()
- test_detect_phone_number()
- test_detect_api_key_openai_format()
- test_detect_api_key_anthropic_format()
- test_detect_person_name() (if NER available)
- test_detect_credit_card_number()
- test_detect_ip_address()
- test_no_pii_returns_empty()
- test_overlapping_spans_resolved()
- test_detect_in_blob_bytes()
- test_min_confidence_filters_low_scores()

Use pytest.importorskip("presidio_analyzer") to skip if not installed.
```

**Acceptance Criteria:**
- [ ] All test cases implemented
- [ ] Tests skip gracefully if dependencies not installed
- [ ] Edge cases covered (empty string, whitespace only, unicode text)

---

## DAY 15–16: Policy Engine & Redaction

### Task 2.4.1: Policy Engine
**Assigned to:** Tier 2 (Claude Haiku 4.5) with Tier 3 review
**Estimated Time:** 3 hours
**Dependencies:** Task 2.3.4
**Deliverable:** `vault/sanitization/policy.py` + `config_examples/policies.yaml`

**RISEN Prompt:**
```
Role: Policy configuration engineer
Context: Need YAML-driven rules controlling how PII is handled per sensitivity level

Instructions:
1. Define policy YAML schema (config_examples/policies.yaml):

   version: 1
   default_action: redact          # redact | mask | flag | allow
   auto_detect_on_import: true     # run detector on every imported message
   min_confidence: 0.75

   rules:
     - pii_types: [EMAIL_ADDRESS, PHONE_NUMBER]
       sensitivity_levels: [INTERNAL, CONFIDENTIAL, RESTRICTED]
       action: redact

     - pii_types: [API_KEY, CREDIT_CARD, US_SSN]
       sensitivity_levels: [PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED]
       action: redact

     - pii_types: [PERSON]
       sensitivity_levels: [CONFIDENTIAL, RESTRICTED]
       action: mask               # replace with [PERSON_1], [PERSON_2], etc.

     - pii_types: [IP_ADDRESS]
       sensitivity_levels: [RESTRICTED]
       action: flag               # mark for review but don't redact

     allowlist:
       - type: EMAIL_ADDRESS
         pattern: ".*@mycompany\\.com$"   # don't redact internal emails

2. Implement PolicyEngine class:
   class PolicyEngine:
       def __init__(self, policy_path: Path):
           self.policy = self._load(policy_path)

       def get_action(
           self,
           pii_type: str,
           sensitivity: SensitivityLevel
       ) -> str:
           """Return 'redact', 'mask', 'flag', or 'allow' for this span."""

       def should_auto_detect(self) -> bool:
           """Whether to run detection on import."""

       def is_allowlisted(self, pii_type: str, text: str) -> bool:
           """Check if matched text is in the allowlist."""

3. Use pydantic to validate the YAML schema on load

Safety:
- Fail-closed: unknown action → treat as 'redact'
- Validate all regex patterns on load
- Log policy load errors clearly
```

**Acceptance Criteria:**
- [ ] YAML schema defined and documented
- [ ] PolicyEngine loads and validates config
- [ ] get_action() returns correct action for each rule
- [ ] Allowlist regex matching works
- [ ] Fail-closed on unknown actions

---

### Task 2.4.2: Redaction Engine
**Assigned to:** Tier 3 (Claude Sonnet 4.5) — Security Critical
**Estimated Time:** 4 hours
**Dependencies:** Task 2.3.4, Task 2.4.1
**Deliverable:** `vault/sanitization/redactor.py`

**RISEN Prompt:**
```
Role: Secure data engineer, expert in text redaction and blob rewriting
Context: Need to apply PII policy decisions to conversation blob content

Instructions:
1. Implement RedactionEngine class:
   class RedactionEngine:
       def __init__(
           self,
           detector: CombinedPIIDetector,
           policy: PolicyEngine,
           blob_store: BlobStore,
           db: VaultDB,
       ):
           ...

       def redact_conversation(
           self,
           conversation_id: str,
           master_key: bytes,
       ) -> RedactionResult:
           """
           Detect and redact PII in all messages of a conversation.

           Steps:
           1. Load all messages from DB
           2. For each message:
              a. Decrypt blob content
              b. Run detector on plaintext
              c. Apply policy to each span
              d. Build redacted text (replace spans with tokens)
              e. Re-encrypt and store to new blob_id
              f. Update message.sanitized_blob_uuid in DB
              g. Write PIIFinding records to DB
           3. Return RedactionResult with counts
           """

       def _apply_redaction(
           self,
           text: str,
           spans: List[PIISpan],
           actions: Dict[PIISpan, str],
       ) -> str:
           """
           Replace PII spans in text.
           - redact: [REDACTED:EMAIL_ADDRESS]
           - mask: [PERSON_1], [PERSON_2] (consistent within conversation)
           - flag: text unchanged, but PIIFinding written
           - allow: text unchanged
           """

2. RedactionResult dataclass:
   @dataclass
   class RedactionResult:
       conversation_id: str
       messages_processed: int
       pii_spans_found: int
       pii_spans_redacted: int
       pii_spans_masked: int
       pii_spans_flagged: int
       errors: List[str]

3. Consistency for masking:
   - Track "John Smith" → [PERSON_1] mapping within a conversation
   - Same name always maps to same token within one conversation
   - Reset mapping per conversation (don't leak across)

4. Atomic blob replacement:
   - Write new (redacted) blob first
   - Update DB to point message.sanitized_blob_uuid at new blob
   - Old raw blob preserved (message.content_blob_uuid unchanged)
   - This means `show` uses sanitized_blob_uuid if it exists

Safety:
- Never log redacted content
- Preserve original blob (non-destructive by default)
- Write PIIFinding to DB for audit trail
- Atomic: if DB update fails, delete new blob
- Validate span offsets before applying (prevent index errors)
```

**Acceptance Criteria:**
- [ ] Redacts email, phone, API keys in blob content
- [ ] Masking consistent within a conversation
- [ ] Original blob preserved (sanitized_blob_uuid is separate)
- [ ] PIIFinding records written to DB
- [ ] RedactionResult returned with accurate counts
- [ ] Atomic blob replacement (no partial state)

---

### Task 2.4.3: Wire PII into Import Pipeline
**Assigned to:** Tier 3 (Claude Sonnet 4.5)
**Estimated Time:** 2 hours
**Dependencies:** Task 2.4.2, Task 2.4.1
**Deliverable:** Update `vault/ingestion/pipeline.py`

**RISEN Prompt:**
```
Role: Integration engineer
Context: Auto-detect PII on import if policy says so

Instructions:
1. Add optional detector + policy + redactor to ImportPipeline.__init__():
   def __init__(
       self,
       db: VaultDB,
       blob_store: BlobStore,
       key_manager: KeyManager,
       detector: CombinedPIIDetector | None = None,
       policy: PolicyEngine | None = None,
   ):

2. In _import_one(), after storing blobs:
   if self.detector and self.policy and self.policy.should_auto_detect():
       redactor = RedactionEngine(self.detector, self.policy, self.blob_store, self.db)
       redactor.redact_conversation(conv_id, master_key)

3. Update CLI import command to optionally pass detector+policy if
   policies.yaml exists in vault_path

4. Add --no-sanitize flag to vault import to skip auto-detection
```

**Acceptance Criteria:**
- [ ] Auto-detection runs on import when policy enables it
- [ ] --no-sanitize flag skips detection
- [ ] Results shown in import summary (PII spans found)
- [ ] Performance: import not more than 2x slower with detection enabled

---

## DAY 17: `vault sanitize` CLI Command

### Task 2.5.1: `vault sanitize` Command
**Assigned to:** Tier 2 (Claude Haiku 4.5)
**Estimated Time:** 2 hours
**Dependencies:** Task 2.4.2
**Deliverable:** Add `sanitize` command to `vault/cli/main.py`

**CARE Prompt:**
```
Context: RedactionEngine exists. Need CLI to trigger it.
Action: Add vault sanitize command
Result: User can redact PII from any conversation on demand
Example:

$ vault sanitize a1b2c3d4
┌─────────────────────────────────────────────┐
│ Sanitizing: Python Async Basics             │
└─────────────────────────────────────────────┘

Running PII detection...
Found 3 PII spans across 12 messages:
  • EMAIL_ADDRESS (confidence: 0.98)
  • API_KEY (confidence: 0.95)
  • PERSON (confidence: 0.87)

Applying policy: redact EMAIL_ADDRESS, API_KEY | mask PERSON

✓ 3 spans redacted/masked
✓ Sanitized content stored (original preserved)

Use `vault show a1b2c3d4 --view sanitized` to see redacted version.

Implement:
@app.command()
def sanitize(
    conversation_id: str,
    dry_run: bool = Option(False, "--dry-run", help="Show what would be redacted without changing anything"),
    policy_path: Path = Option(None, "--policy"),
    vault_path: Path = Option(Path("vault_data")),
):
    """Detect and redact PII in a conversation."""
```

**Acceptance Criteria:**
- [ ] `vault sanitize <id>` works end-to-end
- [ ] `--dry-run` shows what would be redacted without writing
- [ ] Progress display with Rich
- [ ] Summary of spans found and actions taken

---

### Task 2.5.2: Update `vault show` for Sanitized View
**Assigned to:** Tier 2 (GPT-4o-mini)
**Estimated Time:** 1 hour
**Dependencies:** Task 2.5.1
**Deliverable:** Update `vault/cli/main.py`

**CARE Prompt:**
```
Context: vault show currently always reads content_blob_uuid.
         After sanitization, message.sanitized_blob_uuid is set.
Action: Add --view sanitized to vault show command
Result: Users can compare raw and sanitized versions

Changes:
1. Add `sanitized` as a valid --view value
2. If view=sanitized, use message.sanitized_blob_uuid if available,
   otherwise fall back to content_blob_uuid with a warning
3. Add indicator next to each message showing if it's been sanitized
```

**Acceptance Criteria:**
- [ ] `vault show <id> --view sanitized` works
- [ ] Falls back gracefully if not yet sanitized
- [ ] Visual indicator showing sanitized vs raw

---

## DAY 18: Token Vault

### Task 2.6.1: Token Vault Implementation
**Assigned to:** Tier 3 (Claude Sonnet 4.5) — Security Critical
**Estimated Time:** 4 hours
**Dependencies:** Phase 1 crypto module
**Deliverable:** `vault/security/token_vault.py`

**RISEN Prompt:**
```
Role: Cryptographic security engineer
Context: Need encrypted storage for LLM provider API keys and other credentials.
         This is separate from the session token system — it's long-term secret storage.

Instructions:
1. Implement TokenVault class:
   class TokenVault:
       """
       Encrypted key-value store for provider API credentials.

       Each credential is encrypted with a key derived from the master key
       + the credential name (HKDF). Stored at vault_root/tokens/<name>.tok

       Format: Fernet-encrypted JSON:
         {"provider": "openai", "key": "sk-...", "created_at": "..."}
       """
       def __init__(self, vault_root: Path, key_manager: KeyManager):
           self.root = vault_root / "tokens"
           self.km = key_manager
           self.root.mkdir(exist_ok=True)

       def store(self, name: str, provider: str, value: str, master_key: bytes) -> None:
           """Store a credential. Overwrites if already exists."""

       def retrieve(self, name: str, master_key: bytes) -> str | None:
           """Decrypt and return credential value, or None if not found."""

       def delete(self, name: str) -> bool:
           """Securely delete a credential file."""

       def list_names(self) -> list[str]:
           """Return names of all stored credentials (not values)."""

2. Key derivation per credential:
   - HKDF(master_key, salt=name.encode(), info=b"vault-token-credential")
   - Unique key per credential name

3. File format:
   - vault_root/tokens/{name}.tok
   - Fernet-encrypted JSON with metadata
   - Permissions: 0600

4. Validation:
   - name must be alphanumeric + hyphens only
   - value must not be empty
   - provider must be one of known set OR arbitrary string

Safety:
- Never log credential values
- 0600 file permissions
- Atomic write (tmp → rename)
- Secure delete (overwrite before unlink)
```

**Acceptance Criteria:**
- [ ] Credentials stored encrypted at `vault_root/tokens/`
- [ ] Retrieve with correct master key works
- [ ] Retrieve with wrong master key fails
- [ ] Secure delete implemented
- [ ] list_names() only exposes names, not values
- [ ] File permissions 0600

---

### Task 2.6.2: Token Vault CLI Commands
**Assigned to:** Tier 1 (DeepSeek-Coder)
**Estimated Time:** 1.5 hours
**Dependencies:** Task 2.6.1
**Deliverable:** Add `token` sub-commands to `vault/cli/main.py`

**CARE Prompt:**
```
Context: TokenVault class is implemented
Action: Add vault token subcommands using Typer sub-app
Result: User can manage provider API keys

Commands:
  vault token set <name> [--provider openai]     # prompts for value (hidden)
  vault token get <name>                         # confirms before showing
  vault token list                               # shows names only, not values
  vault token delete <name>                      # confirms before deleting

Example:
  $ vault token set openai-key --provider openai
  Enter API key value: ****
  ✓ Credential 'openai-key' stored securely.

  $ vault token list
  ┌──────────────┬──────────┬──────────────────────┐
  │ Name         │ Provider │ Created              │
  ├──────────────┼──────────┼──────────────────────┤
  │ openai-key   │ openai   │ 2026-02-18 10:30 UTC │
  └──────────────┴──────────┴──────────────────────┘

Safety:
- Never echo key values to terminal except on explicit get
- Confirm "Are you sure?" before delete
- Require passphrase/session for all operations
```

**Acceptance Criteria:**
- [ ] All 4 sub-commands work
- [ ] Values never echoed except on `get` with confirmation
- [ ] Session management integrated
- [ ] Rich table formatting

---

## DAY 19: `vault policy` Command + Integration

### Task 2.7.1: `vault policy` CLI Command
**Assigned to:** Tier 1 (Llama3b)
**Estimated Time:** 1 hour
**Dependencies:** Task 2.4.1
**Deliverable:** Add `policy` sub-commands to `vault/cli/main.py`

**CARE Prompt:**
```
Context: PolicyEngine exists, YAML config exists
Action: Add vault policy subcommands
Result: User can view and manage policies

Commands:
  vault policy show                  # display current policy config
  vault policy set-auto-detect on|off  # toggle auto-detection on import

Example output for vault policy show:
  Auto-detect on import: ON
  Min confidence: 0.75
  Rules:
  ┌─────────────────┬─────────────────────────────┬────────┐
  │ PII Types       │ Sensitivity Levels          │ Action │
  ├─────────────────┼─────────────────────────────┼────────┤
  │ EMAIL, PHONE    │ INTERNAL+                   │ redact │
  │ API_KEY, SSN    │ All                         │ redact │
  │ PERSON          │ CONFIDENTIAL+               │ mask   │
  └─────────────────┴─────────────────────────────┴────────┘
```

**Acceptance Criteria:**
- [ ] `vault policy show` displays current config
- [ ] `vault policy set-auto-detect` updates config file
- [ ] Reads from vault_data/policies.yaml (creates default if missing)

---

### Task 2.7.2: Default Policy Config Generation
**Assigned to:** Tier 1 (Qwen)
**Estimated Time:** 30 minutes
**Dependencies:** Task 2.4.1
**Deliverable:** Update `vault init` to write default `policies.yaml`

**CARE Prompt:**
```
Context: vault init creates vault directory structure
Action: Add default policies.yaml generation to vault init
Result: Out-of-the-box policy configuration

Add to vault init command:
  # After DB creation
  policy_path = vault_path / "policies.yaml"
  if not policy_path.exists():
      _write_default_policy(policy_path)

Implement _write_default_policy() to write the example
from config_examples/policies.yaml to vault_path/policies.yaml
```

---

## DAY 20: Final Tests & Security Review

### Task 2.8.1: Sanitization Unit Tests
**Assigned to:** Tier 2 (GPT-4o-mini)
**Estimated Time:** 2 hours
**Dependencies:** All Phase 2 modules
**Deliverable:** `tests/test_sanitization.py`, `tests/test_token_vault.py`, `tests/test_audit.py`

**CARE Prompt:**
```
Context: Sanitization pipeline (detector + policy + redactor) is complete
Action: Write unit tests for all Phase 2 modules
Result: >80% coverage on vault/sanitization/ and vault/security/token_vault.py

Tests needed:
test_sanitization.py:
  - test_redact_email_in_blob()
  - test_mask_person_consistently_within_conversation()
  - test_original_blob_preserved_after_redaction()
  - test_pii_finding_written_to_db()
  - test_dry_run_makes_no_changes()
  - test_allow_rule_preserves_text()

test_token_vault.py:
  - test_store_and_retrieve()
  - test_wrong_key_fails()
  - test_delete_removes_file()
  - test_list_names_only()
  - test_invalid_name_raises()

test_audit.py:
  - test_log_writes_audit_event()
  - test_audit_event_failure_doesnt_crash()
  - test_vault_audit_command_shows_events()
```

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] >80% coverage on new modules
- [ ] Tests isolated (tmp_path, no shared state)

---

### Task 2.8.2: Tier 4 Security Review
**Assigned to:** Tier 4 (Claude Opus 4.5)
**Estimated Time:** 1 hour (single use)
**Dependencies:** All Phase 2 tasks complete
**Deliverable:** Written security review report → `docs/SECURITY_REVIEW_PHASE2.md`

**RISEN Prompt:**
```
Role: Senior cryptographic security reviewer
Context: Phase 2 of LLM Memory Vault is complete.
         The following new security-critical modules have been added:
         - vault/sanitization/ (PII detection + redaction engine)
         - vault/security/token_vault.py (encrypted credential storage)
         - vault/security/audit.py (audit log writer)

Instructions:
Review these modules for:
1. Cryptographic correctness (key derivation per credential, Fernet usage)
2. Information leakage (do logs ever contain plaintext PII or keys?)
3. Side-channel risks (timing attacks on key comparison, oracle attacks)
4. Redaction completeness (can PII be reconstructed from PIIFinding records?)
5. Audit log integrity (can audit events be tampered with?)
6. Dependency security (presidio, llm_guard — any known CVEs?)

Output:
- docs/SECURITY_REVIEW_PHASE2.md
- Executive summary (1 paragraph)
- Per-module findings table
- Risk ratings (Critical / High / Medium / Low / Info)
- Specific remediation recommendations
```

**Acceptance Criteria:**
- [ ] All Critical and High findings addressed before Phase 3
- [ ] Report committed to docs/
- [ ] No new attack surface introduced

---

## Testing Strategy

### Unit Tests (per module — Tier 2)
| Test File | Module | Est. Time |
|-----------|--------|-----------|
| `test_pii_detection.py` | presidio + llmguard + combined | 2h |
| `test_sanitization.py` | redactor + policy | 2h |
| `test_token_vault.py` | token vault | 1h |
| `test_audit.py` | audit logger | 1h |

### Integration Tests (Tier 3 — Task 2.1.1)
End-to-end: init → import (with auto-sanitize) → sanitize → show sanitized

### Performance Baseline
Run before and after each task:
```bash
poetry run python -m timeit -n 3 "from vault.sanitization.detector import CombinedPIIDetector; d = CombinedPIIDetector(); d.detect('Contact john@example.com or call 07911 123456')"
```
Target: <200ms per conversation detection

---

## Execution Order (Critical Path)

```
Day 11: Task 2.1.1 (Integration Tests)                    ← Tier 3, parallel with Day 12
Day 12: Task 2.2.1 (Audit logging)                        ← Tier 2
Day 13: Task 2.3.1 (PII base interface) THEN              ← Tier 2
         Task 2.3.2 (Presidio) + Task 2.3.3 (LLMGuard)   ← Tier 3 (can run in parallel)
Day 14: Task 2.3.4 (Combined detector)                    ← Tier 3 (needs 2.3.2 + 2.3.3)
         Task 2.3.5 (PII tests)                           ← Tier 2 (can run in parallel with 2.3.4)
Day 15: Task 2.4.1 (Policy engine)                        ← Tier 2
         Task 2.4.2 (Redaction engine)                    ← Tier 3 (needs 2.4.1 + 2.3.4)
Day 16: Task 2.4.3 (Wire PII into pipeline)               ← Tier 3
Day 17: Task 2.5.1 (vault sanitize CLI)                   ← Tier 2
         Task 2.5.2 (vault show sanitized view)           ← Tier 2 (parallel)
Day 18: Task 2.6.1 (Token vault)                          ← Tier 3
         Task 2.6.2 (Token vault CLI)                     ← Tier 1 (after 2.6.1)
Day 19: Task 2.7.1 (vault policy CLI)                     ← Tier 1
         Task 2.7.2 (Default policy in init)              ← Tier 1 (parallel)
Day 20: Task 2.8.1 (All Phase 2 tests)                    ← Tier 2
         Task 2.8.2 (Security review)                     ← Tier 4
```

**Parallelisable pairs (run on same day):**
- 2.3.2 + 2.3.3 (Presidio and LLM Guard — independent)
- 2.5.1 + 2.5.2 (sanitize command and show update — independent)
- 2.6.2 + 2.7.1 + 2.7.2 (all Tier 1 CLI tasks — independent)
- 2.8.1 + 2.8.2 (tests and security review — independent)

---

## Risk Management

### Risk 1: Presidio Model Download Failures
- **Probability:** Medium (large spaCy model, ~50MB)
- **Impact:** Medium (blocks Day 13)
- **Mitigation:** Cache in `~/.cache/vault/models/`; retry logic; fallback to regex-only mode
- **Owner:** Task 2.3.2

### Risk 2: LLM Guard / Transformers Dependency Conflicts
- **Probability:** High (transformers has heavy deps)
- **Impact:** Medium (NER falls back to pattern-only mode)
- **Mitigation:** Make LLM Guard optional; pattern-only is still >95% recall
- **Owner:** Task 2.3.3

### Risk 3: PII Detection False Positives Corrupting Data
- **Probability:** Low-Medium
- **Impact:** High (redaction is non-reversible on sanitized blob)
- **Mitigation:** Original blob always preserved; `--dry-run` flag; min confidence threshold; policy allowlist
- **Owner:** Task 2.4.2

### Risk 4: Redaction Performance (slow on large conversations)
- **Probability:** Medium (NER is slow on CPU)
- **Impact:** Medium (import takes minutes instead of seconds)
- **Mitigation:** Auto-detect optional (policy-controlled); batch messages; run in background
- **Owner:** Task 2.4.3

### Risk 5: Token Vault Key Derivation Collision
- **Probability:** Very Low
- **Impact:** High (wrong key could decrypt another credential)
- **Mitigation:** HKDF with distinct `info` bytes per credential; Tier 4 review
- **Owner:** Task 2.6.1

---

## Resource Allocation Summary

| Tier | Tasks | Est. Hours | Est. Cost |
|------|-------|------------|-----------|
| Tier 1 (Local) | 2.6.2, 2.7.1, 2.7.2 | 3 | $0 |
| Tier 2 (Haiku) | 2.2.1, 2.3.1, 2.3.5, 2.4.1, 2.5.1, 2.5.2, 2.8.1 | 14 | ~$2 |
| Tier 3 (Sonnet) | 2.1.1, 2.3.2, 2.3.3, 2.3.4, 2.4.2, 2.4.3, 2.6.1 | 22 | ~$20 |
| Tier 4 (Opus) | 2.8.2 | 1 | ~$5 |
| **Total** | **17 tasks** | **40h** | **~$27** |

---

## Success Criteria Checklist

### Milestone 2.1 ✅ Integration Tests & Audit
- [ ] 5 integration test scenarios passing
- [ ] Audit events written for all vault operations
- [ ] `vault audit` command working

### Milestone 2.2 ✅ PII Detection
- [ ] Presidio detector live
- [ ] LLM Guard NER detector live (or graceful fallback)
- [ ] Combined detector merging results
- [ ] Unit tests passing

### Milestone 2.3 ✅ Policy & Redaction
- [ ] Policy YAML loaded and evaluated
- [ ] Redaction engine rewrites blobs
- [ ] Original blobs preserved
- [ ] PIIFinding records in DB
- [ ] Auto-detection on import working

### Milestone 2.4 ✅ Token Vault & CLI
- [ ] `vault sanitize <id>` working
- [ ] `vault show --view sanitized` working
- [ ] `vault token set/get/list/delete` working
- [ ] `vault policy show` working
- [ ] All unit tests passing (>80% coverage)
- [ ] Tier 4 security review complete

### Phase 2 Complete ✅
- [ ] >99% PII recall on test corpus
- [ ] Zero known Critical/High security findings
- [ ] All tests passing in CI
- [ ] Documentation updated
- [ ] Ready for Phase 3

---

## Handoff to Phase 3

**Phase 3 Focus:** Classification & Distillation
- Domain taxonomy tagging (Life / Work / Home / System / Ideas) — see `docs/intro/PROJECT 1 - AI Local Memory Bank.txt`
- Local LLM distillation via Ollama (`vault distill <id>`)
- Conversation summarisation and key-point extraction
- Multi-label classifier for domain tagging
- `vault classify`, `vault distill`, `vault search` (text) CLI commands

**Prerequisites for Phase 3:**
1. Phase 2 tests all passing
2. Tier 4 security review signed off
3. Ollama installed and running locally (user setup)
4. Token vault used to store Ollama endpoint config

---

*Last Updated: 2026-02-18*
*Phase 2 Status: READY TO START*
*Estimated Completion: 2026-03-04 (10 working days from 2026-02-18)*
