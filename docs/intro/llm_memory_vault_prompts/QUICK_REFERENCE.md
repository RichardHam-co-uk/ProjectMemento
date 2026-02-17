# LLM Memory Vault - Quick Reference Card

## 🚀 Start Here (3 Steps)

### 1. Setup (5 minutes)
```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Set API key
export ANTHROPIC_API_KEY="your-key"

# Install Poetry (if needed)
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Read Docs (10 minutes)
```bash
# Read getting started guide
cat GETTING_STARTED.md

# Skim phase 1 plan
cat PHASE1_DETAILED_PLAN.md
```

### 3. Start Building (Day 1)
```bash
# Create project
mkdir llm_memory_vault
cd llm_memory_vault

# Execute first task
claude-code --file ../llm_memory_vault_prompts/tasks/task_1.1.1_repository_structure.txt
```

---

## 📋 Daily Checklist

### Every Morning
- [ ] Review yesterday's daily log
- [ ] Check checklist.md for today's tasks
- [ ] Review budget in cost_tracker.md

### During Work
- [ ] Execute tasks in order
- [ ] Validate acceptance criteria
- [ ] Commit after each task
- [ ] Update checklist.md

### Every Evening
- [ ] Update daily_log.md
- [ ] Log costs in cost_tracker.md
- [ ] Plan tomorrow's tasks
- [ ] Git push (if using remote)

---

## 🎯 Task Execution Pattern

```bash
# 1. Execute task
claude-code --file tasks/task_X.Y.Z_name.txt

# 2. Review output
git status
ls -la

# 3. Test if applicable
poetry run pytest

# 4. Commit
git add .
git commit -m "Task X.Y.Z: Description"

# 5. Update tracking
nano tracking/checklist.md  # Mark complete
nano tracking/cost_tracker.md  # Log cost

# 6. Next task
```

---

## 🗂️ File Locations

| What | Where |
|------|-------|
| Task prompts | `tasks/task_*.txt` |
| Getting started | `GETTING_STARTED.md` |
| Full plan | `PHASE1_DETAILED_PLAN.md` |
| Task checklist | `tracking/checklist.md` |
| Cost tracker | `tracking/cost_tracker.md` |
| Daily log | `tracking/daily_log.md` |
| Config examples | `reference/*.yaml` |

---

## 📅 Timeline (10 Days)

**Days 1-2:** Project setup (Tasks 1.1.x, 1.2.x)  
**Days 3-5:** Encryption & DB (Tasks 1.3.x, 1.4.x, 1.5.x)  
**Days 6-8:** Ingestion (Tasks 1.6.x, 1.8.x)  
**Days 9-10:** CLI polish (Tasks 1.9.x)

---

## 💰 Budget Tracking

| Tier | Model | Estimated | Track In |
|------|-------|-----------|----------|
| 1 | Local (Ollama) | $0 | cost_tracker.md |
| 2 | Haiku/GPT-4o-mini | ~$2 | cost_tracker.md |
| 3 | Sonnet 4.5 | ~$15 | cost_tracker.md |
| **Total** | | **~$17** | |

---

## 🔒 Security Tasks (Use Tier 3)

- Task 1.3.1: Key Derivation
- Task 1.3.2: Blob Storage
- Task 1.5.1: Session Tokens

---

## ✅ Phase 1 Success Criteria

At completion, you should have:
- [x] Functional `vault` CLI
- [x] Encryption working
- [x] 100+ conversations imported
- [x] Commands: init, import, list, show, stats
- [x] Tests passing
- [x] Ready for Phase 2

---

## 🆘 Quick Troubleshooting

**Poetry install fails:**
```bash
poetry cache clear pypi --all
poetry install
```

**Claude Code not found:**
```bash
npm install -g @anthropic-ai/claude-code
```

**Pre-commit hooks fail:**
```bash
poetry run pre-commit run --all-files
# Fix issues, then commit
```

**Wrong passphrase:**
```bash
vault lock  # Clear session
vault init --force  # Re-initialize (WARNING: loses data!)
```

---

## 📞 Support

- Full docs: `GETTING_STARTED.md`
- Architecture: `PHASE1_DETAILED_PLAN.md`
- Examples: `reference/` directory
- Tracking: `tracking/` directory

---

**Ready to build? Start with:**
```bash
cat GETTING_STARTED.md
claude-code --file tasks/task_1.1.1_repository_structure.txt
```

Good luck! 🎉
