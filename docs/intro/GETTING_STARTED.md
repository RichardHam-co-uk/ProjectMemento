# LLM Memory Vault - Claude Code Execution Guide

## 🚀 Quick Start

This guide will help you execute Phase 1 of the LLM Memory Vault project using Claude Code.

## Prerequisites

### 1. Install Claude Code
```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Verify installation
claude-code --version
```

### 2. Set Up API Key
```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Or add to ~/.bashrc or ~/.zshrc for persistence
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
```

### 3. Prepare Local LLMs (Optional - for Tier 1 tasks)
```bash
# Install Ollama for local LLM execution
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended models
ollama pull llama3.1:8b
ollama pull deepseek-coder:6.7b
ollama pull qwen2.5-coder:7b
```

### 4. Create Project Repository
```bash
# Option 1: Use your template
git clone https://github.com/zebadee2kk/best-practice-repo-template.git llm_memory_vault
cd llm_memory_vault

# Option 2: Start from scratch
mkdir llm_memory_vault
cd llm_memory_vault
git init
```

---

## 📋 Execution Workflow

### Step 1: Review the Plan
```bash
# Read the detailed Phase 1 plan
cat PHASE1_DETAILED_PLAN.md
```

### Step 2: Execute Tasks in Order

Each task has a corresponding prompt file in `tasks/` directory.

**Format:** `task_<day>.<task>_<name>.txt`

**Example execution:**
```bash
# Navigate to project directory
cd llm_memory_vault

# Execute Task 1.1.1 (Project Scaffolding)
claude-code --file ../llm_memory_vault_prompts/tasks/task_1.1.1_repository_structure.txt

# Review output
git status

# Validate acceptance criteria (see tracking/checklist.md)

# Commit changes
git add .
git commit -m "Task 1.1.1: Project scaffolding complete"

# Move to next task
claude-code --file ../llm_memory_vault_prompts/tasks/task_1.1.2_dependencies.txt
```

### Step 3: Validate After Each Task

Before moving to the next task:
1. ✅ Check acceptance criteria in `tracking/checklist.md`
2. ✅ Run any tests if applicable
3. ✅ Commit to git
4. ✅ Update progress tracker

---

## 🎯 Task Execution Order

### Day 1: Project Setup
```bash
claude-code --file tasks/task_1.1.1_repository_structure.txt
claude-code --file tasks/task_1.1.2_dependencies.txt
claude-code --file tasks/task_1.1.3_config_models.txt
claude-code --file tasks/task_1.1.4_precommit_hooks.txt
```

### Day 2: Core Data Models
```bash
claude-code --file tasks/task_1.2.1_orm_models.txt
claude-code --file tasks/task_1.2.2_migrations.txt
```

### Day 3: Encryption & Blob Storage
```bash
claude-code --file tasks/task_1.3.1_key_derivation.txt
claude-code --file tasks/task_1.3.2_blob_storage.txt
```

### Day 4: Database Setup & CLI Init
```bash
claude-code --file tasks/task_1.4.1_database_wrapper.txt
claude-code --file tasks/task_1.4.2_cli_init.txt
```

### Day 5: Session Management
```bash
claude-code --file tasks/task_1.5.1_session_tokens.txt
claude-code --file tasks/task_1.5.2_cli_session_integration.txt
```

### Day 6-7: ChatGPT Ingestion
```bash
claude-code --file tasks/task_1.6.1_base_adapter.txt
claude-code --file tasks/task_1.6.2_chatgpt_adapter.txt
```

### Day 8: Import Integration
```bash
claude-code --file tasks/task_1.8.1_import_pipeline.txt
claude-code --file tasks/task_1.8.2_cli_import_command.txt
```

### Day 9-10: Basic Retrieval & CLI Polish
```bash
claude-code --file tasks/task_1.9.1_cli_list.txt
claude-code --file tasks/task_1.9.2_cli_show.txt
claude-code --file tasks/task_1.9.3_cli_stats.txt
claude-code --file tasks/task_1.9.4_error_handling.txt
```

---

## 🔧 Claude Code Options

### Basic Execution
```bash
# Execute a single prompt file
claude-code --file tasks/task_1.1.1_repository_structure.txt
```

### Advanced Options
```bash
# Use specific model (default: claude-sonnet-4.5)
claude-code --model claude-opus-4.5 --file tasks/task_1.3.1_key_derivation.txt

# Interactive mode (for complex tasks)
claude-code --interactive

# Specify output directory
claude-code --output-dir /path/to/project --file tasks/task_1.1.1_repository_structure.txt

# Dry run (see what would be done)
claude-code --dry-run --file tasks/task_1.1.1_repository_structure.txt
```

### Using Local LLMs (Tier 1 Tasks)
```bash
# For simple tasks, use local Ollama models
# Edit the task file to use Ollama endpoint instead

# Or use direct API
curl http://localhost:11434/api/generate -d '{
  "model": "deepseek-coder:6.7b",
  "prompt": "$(cat tasks/task_1.1.1_repository_structure.txt)"
}'
```

---

## 📊 Progress Tracking

### Update Checklist
```bash
# After each task, update the checklist
nano tracking/checklist.md

# Mark task as complete
# Update time spent
# Note any blockers
```

### Track Costs
```bash
# Log LLM costs in the tracker
nano tracking/cost_tracker.md

# Format:
# Task | Model | Input Tokens | Output Tokens | Cost | Notes
```

### Daily Summary
```bash
# At end of each day, review progress
cat tracking/daily_log.md

# Add new entry:
echo "## Day 1 - $(date)" >> tracking/daily_log.md
echo "### Completed Tasks:" >> tracking/daily_log.md
echo "- Task 1.1.1: Repository structure ✅" >> tracking/daily_log.md
```

---

## 🧪 Testing

### Run Tests After Each Module
```bash
# Install test dependencies
poetry install --with dev

# Run unit tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_crypto.py -v

# Check coverage
poetry run pytest --cov=vault tests/
```

### Pre-Commit Checks
```bash
# Run before committing
poetry run pre-commit run --all-files

# Auto-fix formatting
poetry run black vault/
poetry run ruff check --fix vault/
```

---

## 🚨 Troubleshooting

### Claude Code Not Finding Files
```bash
# Make sure you're in the project directory
cd llm_memory_vault

# Use absolute paths if needed
claude-code --file /absolute/path/to/tasks/task_1.1.1_repository_structure.txt
```

### API Key Issues
```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Test with simple prompt
claude-code --prompt "Hello, test connection"
```

### Local LLM Issues
```bash
# Check Ollama is running
ollama list

# Test model
ollama run deepseek-coder:6.7b "print('hello world')"

# Pull model if missing
ollama pull deepseek-coder:6.7b
```

### Poetry Issues
```bash
# Install Poetry if missing
curl -sSL https://install.python-poetry.org | python3 -

# Clear cache and reinstall
poetry cache clear pypi --all
poetry install
```

---

## 📁 File Structure Overview

```
llm_memory_vault_prompts/
├── GETTING_STARTED.md          ← You are here
├── PHASE1_DETAILED_PLAN.md     ← Complete phase 1 plan
├── tasks/                      ← Individual prompt files (19 files)
│   ├── task_1.1.1_repository_structure.txt
│   ├── task_1.1.2_dependencies.txt
│   ├── task_1.1.3_config_models.txt
│   └── ...
├── reference/                  ← Supporting documents
│   ├── chatgpt_export_format.json
│   ├── config_examples.yaml
│   ├── taxonomy.yaml
│   └── policies.yaml
└── tracking/                   ← Progress tracking
    ├── checklist.md           ← Task completion checklist
    ├── cost_tracker.md        ← LLM cost tracking
    └── daily_log.md           ← Daily progress log

llm_memory_vault/               ← Your actual project (created by tasks)
├── vault/                      ← Python package
├── tests/                      ← Test files
├── pyproject.toml             ← Dependencies
└── README.md                  ← Documentation
```

---

## 🎯 Success Criteria

### After Each Milestone

**Milestone 1.1 (Days 1-2):**
```bash
# Should work:
poetry install
vault --help
pre-commit run --all-files

# Git should show:
git status
# All files committed, clean working tree
```

**Milestone 1.2 (Days 3-5):**
```bash
# Should work:
vault init
# Vault initialized successfully

ls vault_data/
# .salt, vault.db, config.yaml, blobs/
```

**Milestone 1.3 (Days 6-8):**
```bash
# Should work:
vault import chatgpt ~/Downloads/conversations.json
# 100+ conversations imported

vault list
# Table of conversations displayed
```

**Milestone 1.4 (Days 9-10):**
```bash
# Should work:
vault show <conversation-id>
vault stats
# All CLI commands functional
```

---

## 💡 Tips

### 1. Work Incrementally
- Complete one task at a time
- Validate before moving on
- Commit frequently

### 2. Review AI Output
- Don't blindly accept generated code
- Check security-critical sections carefully
- Test edge cases

### 3. Use Git Effectively
```bash
# Create feature branch per task
git checkout -b task/1.1.1-scaffolding

# Commit with descriptive messages
git commit -m "Task 1.1.1: Add project structure

- Created all package directories
- Added __init__.py files
- Configured .gitignore
- Acceptance criteria: ✅ All met"

# Merge back to main
git checkout main
git merge task/1.1.1-scaffolding
```

### 4. Document As You Go
```bash
# Add comments explaining non-obvious code
# Update README.md with setup instructions
# Document any deviations from plan
```

---

## 🆘 Getting Help

### If You Get Stuck:
1. Review the PHASE1_DETAILED_PLAN.md for context
2. Check acceptance criteria in tracking/checklist.md
3. Review reference files for examples
4. Ask Claude for clarification (not Claude Code)

### Common Issues:

**"Task output doesn't match acceptance criteria"**
- Review the RISEN prompt carefully
- Check if dependencies were completed correctly
- Try regenerating with more specific constraints

**"Security concern with generated code"**
- Flag it immediately
- Use Tier 3 (Claude Sonnet) or Tier 4 (Claude Opus) for review
- Reference vault/security/ for best practices

**"Performance issues"**
- Profile the code
- Check against performance targets in plan
- Consider optimization in later phase if not critical

---

## 📞 Next Steps

1. ✅ Read this guide completely
2. ✅ Install prerequisites (Claude Code, Poetry, Ollama)
3. ✅ Review PHASE1_DETAILED_PLAN.md
4. ✅ Start with Task 1.1.1
5. ✅ Update tracking/checklist.md after each task
6. ✅ Celebrate milestone completions! 🎉

---

**Ready to build?** Start with:
```bash
claude-code --file tasks/task_1.1.1_repository_structure.txt
```

Good luck! 🚀
