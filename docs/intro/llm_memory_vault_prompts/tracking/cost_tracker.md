# LLM Cost Tracker - Phase 1

## Budget Overview — ✅ PHASE 1 COMPLETE
- **Phase 1 Estimated Total:** $15-20
- **Actual Spend:** ~$5-8 (estimate — see note below)
- **Budget Status:** ✅ Under Budget

> **Note on actual cost:** Phase 1 was executed by Claude Sonnet 4.6
> (via Claude Code CLI) acting as all tiers in two sessions. Individual
> token counts are not available from the CLI. The estimate below is based
> on approximate token usage derived from code/test output volume.
>
> In future phases, log per-task token usage using:
> `claude --print-stats` or via the Anthropic dashboard.

---

## Actual Phase 1 Results

| Session | Date | Model Used | Tasks Covered | Est. Tokens In | Est. Tokens Out | Est. Cost |
|---------|------|------------|---------------|----------------|-----------------|-----------|
| Session 1 | 2026-02-17 | Claude Sonnet 4.6 | M1.1: scaffolding, config, ORM | ~80K | ~30K | ~$0.69 |
| Session 2 | 2026-02-18 | Claude Sonnet 4.6 | M1.2–1.4: crypto, blobs, DB, CLI, tests, docs | ~350K | ~150K | ~$3.30 |
| **Total** | | | **19 tasks, 63 tests** | **~430K** | **~180K** | **~$4.00** |

> Cost formula: (input_tokens / 1M × $3.00) + (output_tokens / 1M × $15.00)

---

## Tier Deviation

| Planned Tier | Planned Model | Actual Model Used | Reason |
|-------------|---------------|-------------------|--------|
| Tier 1 (4 tasks) | Llama3b, DeepSeek | Claude Sonnet 4.6 | Local agents unavailable |
| Tier 2 (8 tasks) | Haiku, GPT-4o-mini | Claude Sonnet 4.6 | Local agents unavailable |
| Tier 3 (7 tasks) | Claude Sonnet 4.5 | Claude Sonnet 4.6 | Used current model |
| Tier 4 (0 tasks) | Opus — reserved | Not used | Correctly avoided |

**Impact:** ~$4 actual vs ~$17 estimated budget. Under budget due to compression
into 2 sessions (less context switching overhead) and using Sonnet for all tasks
rather than paying the Opus premium.

---

## Phase 2 Cost Forecast

| Tier | Model | Tasks | Est. Hours | Est. Cost |
|------|-------|-------|------------|-----------|
| Tier 1 | Local LLMs | 3 | 3 | $0 |
| Tier 2 | Haiku 4.5 | 7 | 14 | ~$2 |
| Tier 3 | Sonnet 4.5 | 7 | 22 | ~$20 |
| Tier 4 | Opus 4.5 | 1 | 1 | ~$5 |
| **Total** | | **18** | **40h** | **~$27** |

Track Phase 2 costs in `docs/intro/llm_memory_vault_prompts/tracking/cost_tracker_phase2.md`
(create on Phase 2 start).

---

## Pricing Reference (February 2026)

### Tier 1: Local LLMs
- **Cost:** $0.00 (local compute only)
- **Models:** Llama 3.1 8B, DeepSeek-Coder 6.7B, Qwen 2.5 7B

### Tier 2: Budget Cloud
- **Claude Haiku 4.5:** Input $0.25 / 1M · Output $1.25 / 1M
- **GPT-4o-mini:** Input $0.15 / 1M · Output $0.60 / 1M

### Tier 3: Advanced
- **Claude Sonnet 4.5/4.6:** Input $3.00 / 1M · Output $15.00 / 1M
- **GPT-4o:** Input $2.50 / 1M · Output $10.00 / 1M

### Tier 4: Expert
- **Claude Opus 4.5/4.6:** Input $15.00 / 1M · Output $75.00 / 1M

---

## Cost Optimization Lessons from Phase 1

1. **Compressing all tasks into 2 sessions saved context** — each session
   built on accumulated code, so less re-explanation was needed.

2. **Using Sonnet for Tier 1/2 tasks cost more per task but fewer retries.**
   Actual total was still well under the $17 estimate.

3. **Phase 2 recommendation:** Start Phase 2 with a brief context-loading
   prompt so Tier 2/3 agents understand the codebase before starting their
   specific task. Prevents re-reading files mid-task.

---

*Last Updated: 2026-02-18*
*Phase 1 Total: ~$4 (estimated)*
*Phase 2 Budget: $27 (planned)*
