# Project Roadmap

## Phase 1: Foundation & ChatGPT Import (Weeks 1–4) — ✅ COMPLETE (2026-02-18)
- [x] Repository scaffolding and AI readiness
- [x] Poetry project with all dependencies (`pyproject.toml`)
- [x] Pydantic configuration models and pre-commit hooks
- [x] SQLAlchemy ORM models and migration system
- [x] Argon2id key derivation and Fernet encryption
- [x] Encrypted blob storage
- [x] Database wrapper and `vault init` CLI command
- [x] Session token management (30-min expiry)
- [x] Base ingestion adapter and ChatGPT JSON adapter
- [x] Import pipeline with deduplication
- [x] CLI commands: `init`, `import`, `list`, `show`, `stats`
- [x] Error handling and edge case coverage
- [x] Unit test suite — 63 tests, all passing

**Deliverable:** ✅ Import 100+ ChatGPT conversations into encrypted local storage.
**Plan:** `docs/intro/PHASE1_DETAILED_PLAN_1.md`
**Handover:** `docs/HANDOVER_CHECKPOINT_M1.4.md`

---

## Phase 2: Security & Sanitisation (Weeks 5–6) — 🔄 NEXT
- [ ] Integration test suite (end-to-end workflow)
- [ ] Audit logging (all vault operations → AuditEvent table)
- [ ] PII detection engine (Presidio pattern-based + LLM Guard NER)
- [ ] Policy engine (YAML-driven rules per sensitivity level)
- [ ] Redaction engine (blob rewriting with masked tokens)
- [ ] Token vault (encrypted credential storage for provider API keys)
- [ ] `vault sanitize`, `vault token`, `vault policy`, `vault audit` CLI commands
- [ ] Tier 4 security review

**Deliverable:** >99% PII detection rate on test corpus; full audit trail.
**Plan:** `docs/intro/PHASE2_DETAILED_PLAN.md`

---

## Phase 3: Classification & Distillation (Weeks 7–8)
- [ ] Taxonomy system (Life / Work / Home / System / Ideas — see `docs/intro/PROJECT 1`)
- [ ] Local LLM distillation pipeline (Ollama)
- [ ] Tag generation and multi-label classification
- [ ] Conversation summarisation and key-point extraction
- [ ] `vault classify`, `vault distill` CLI commands

**Deliverable:** >95% classification accuracy.

---

## Phase 4: Vector Search (Weeks 9–10)
- [ ] Qdrant collection setup
- [ ] Embedding generation (local sentence-transformers)
- [ ] Hybrid search (BM25 + vector)
- [ ] Metadata filtering and query optimisation
- [ ] `vault search` CLI command

**Deliverable:** <100ms query latency, >90% recall.

---

## Phase 5: API & Integration (Weeks 11–12)
- [ ] FastAPI REST server with CRUD and search routes
- [ ] Authentication (JWT) and rate limiting
- [ ] Redis caching layer
- [ ] OpenAPI documentation
- [ ] CLI tool polish and completions

**Deliverable:** Functional API with full documentation.

---

## Phase 6: Production Hardening (Weeks 13+)
- [ ] Proxmox LXC/VM deployment configuration
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Backup automation and restore workflows
- [ ] Performance optimisation and benchmarking
- [ ] User documentation

**Deliverable:** Production-ready system deployed on Proxmox.
