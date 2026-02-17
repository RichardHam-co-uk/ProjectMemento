# Project Roadmap

## Phase 1: Foundation & ChatGPT Import (Weeks 1–4) — Current
- [x] Repository scaffolding and AI readiness
- [ ] Poetry project with all dependencies (`pyproject.toml`)
- [ ] Pydantic configuration models and pre-commit hooks
- [ ] SQLAlchemy ORM models and migration system
- [ ] Argon2id key derivation and Fernet encryption
- [ ] Encrypted blob storage
- [ ] Database wrapper and `vault init` CLI command
- [ ] Session token management (30-min expiry)
- [ ] Base ingestion adapter and ChatGPT JSON adapter
- [ ] Import pipeline with deduplication
- [ ] CLI commands: `init`, `import`, `list`, `show`, `stats`
- [ ] Error handling and edge case coverage

**Deliverable:** Import 100+ ChatGPT conversations into encrypted local storage.

## Phase 2: Security & Sanitisation (Weeks 5–6)
- [ ] PII detection engine (Presidio pattern-based + LLM Guard NER)
- [ ] Policy engine (YAML-driven rules)
- [ ] Token vault with encryption
- [ ] Audit logging
- [ ] Adversarial input testing

**Deliverable:** >99.5% PII detection rate on test corpus.

## Phase 3: Classification & Distillation (Weeks 7–8)
- [ ] Taxonomy system (Life / Work / Home / System / Ideas)
- [ ] Local LLM distillation pipeline (Ollama)
- [ ] Tag generation and multi-label classification
- [ ] Conversation summarisation and key-point extraction

**Deliverable:** >95% classification accuracy.

## Phase 4: Vector Search (Weeks 9–10)
- [ ] Qdrant collection setup
- [ ] Embedding generation (local sentence-transformers)
- [ ] Hybrid search (BM25 + vector)
- [ ] Metadata filtering and query optimisation

**Deliverable:** <100ms query latency, >90% recall.

## Phase 5: API & Integration (Weeks 11–12)
- [ ] FastAPI REST server with CRUD and search routes
- [ ] Authentication (JWT) and rate limiting
- [ ] Redis caching layer
- [ ] OpenAPI documentation
- [ ] CLI tool polish

**Deliverable:** Functional API with full documentation.

## Phase 6: Production Hardening (Weeks 13+)
- [ ] Proxmox LXC/VM deployment configuration
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Backup automation and restore workflows
- [ ] Performance optimisation and benchmarking
- [ ] User documentation

**Deliverable:** Production-ready system deployed on Proxmox.
