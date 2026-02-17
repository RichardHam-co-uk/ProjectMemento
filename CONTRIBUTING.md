# Contributing to Project Memento

Thank you for considering contributing to Project Memento! This project uses a "Vibe Coding" approach with a tiered LLM structure.

## Tiered LLM Development

We use different AI models for different tasks to optimise cost and quality:

| Tier | Models | Use For |
|------|--------|---------|
| **Tier 1** (Local — Ollama) | Llama3b, DeepSeek-Coder, Qwen | Boilerplate, formatting, simple logic |
| **Tier 2** (Budget Cloud) | GPT-4o-mini, Claude Haiku 4.5 | Docs, tests, adapters |
| **Tier 3** (Advanced) | Claude Sonnet 4.5, GPT-4o | Security, architecture, complex logic |
| **Tier 4** (Expert) | Claude Opus, Perplexity | Security review, research (sparingly) |

## How Can I Contribute?

### Reporting Bugs
- **Check the Issues**: Someone might have already reported it.
- **Open an Issue**: Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).
- **Be Descriptive**: Include steps to reproduce, expected vs. actual behaviour, and environment details.

### Suggesting Enhancements
- **Check the Roadmap**: We might already have it planned.
- **Open an Issue**: Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).

### Pull Requests
1. **Fork the repo** and create your branch from `main`.
2. **Follow the Style Guide**: See [Development Playbook](./docs/playbooks/development.md).
3. **Write Tests**: If you add code, add tests.
4. **Update Docs**: Ensure README and other docs reflect your changes.
5. **Detailed PR**: Use the [PR Template](.github/PULL_REQUEST_TEMPLATE.md).

## Development Workflow

1. **Select Task**: Pick a task from [PHASE1_DETAILED_PLAN_1.md](docs/intro/PHASE1_DETAILED_PLAN_1.md).
2. **Execute**: Feed the prompt file (from `docs/intro/llm_memory_vault_prompts/tasks/`) to Claude Code.
3. **Review**: Check against acceptance criteria.
4. **Test**: Run `poetry run pytest tests/ -v`.
5. **Commit**: Use Conventional Commits (see [Development Playbook](./docs/playbooks/development.md)).

## Quick Setup

```bash
git clone https://github.com/zebadee2kk/ProjectMemento.git
cd ProjectMemento
poetry install
poetry run pre-commit install
poetry run pytest tests/ -v
```

## AI-Assisted Contributions

- **Branch naming**: Use `ai/<short-topic>` for AI-assisted work.
- **Human sponsor**: A human contributor must own the PR and be accountable for the final changes.
- **Disclosure**: Note AI usage in the PR template and summarise prompts or tools used.
- **Verification**: The human sponsor confirms tests, security checks, and reviews are complete.
- **No secrets**: Never include secrets or private data in AI prompts or outputs.

## Style Guide

- **Python**: Follow PEP 8. Use `black` and `ruff`.
- **Type Hints**: Mandatory for all public functions.
- **Docstrings**: Google Style docstrings required.

## Security

- **Never commit secrets**.
- **Run PII checks** before pushing data (handled by pre-commit).
- See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Code of Conduct

By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
