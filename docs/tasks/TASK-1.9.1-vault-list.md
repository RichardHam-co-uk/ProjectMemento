# Task 1.9.1: vault list Command

**Target file:** `vault/cli/main.py` (add to existing)
**Recommended model:** Qwen2.5-Coder or GitHub Copilot
**Effort:** Small (~45 min)
**Dependencies:** `vault/storage/db.py` must exist (Task 1.4.1)

---

## Context

The vault CLI needs a `list` command that shows imported conversations in a Rich table. The `VaultDB` class provides `list_conversations()` and `count_conversations()` methods.

**IMPORTANT:** By the time you work on this task, `vault/cli/main.py` will already have `init`, `lock`, and `import` commands. You are ADDING a new command to the existing file — do NOT overwrite it. Read the file first.

## Files to Read First
- `vault/cli/main.py` — the existing CLI (read to understand the pattern)
- `vault/storage/db.py` — the VaultDB class and its methods

## Requirements

Add a `list` command to the existing Typer app:

```python
@app.command("list")
def list_conversations(
    limit: int = typer.Option(20, help="Number of conversations to show"),
    offset: int = typer.Option(0, help="Skip N conversations"),
    source: str = typer.Option(None, help="Filter by source (e.g., 'chatgpt')"),
    vault_path: Path = typer.Option(Path("vault_data"), help="Path to vault"),
) -> None:
    """List conversations stored in the vault."""
```

### Display Format
Use a Rich Table:
```
┌──────────┬────────────────────────────────────────┬──────────┬────────────┬──────┐
│ ID       │ Title                                  │ Source   │ Date       │ Msgs │
├──────────┼────────────────────────────────────────┼──────────┼────────────┼──────┤
│ a3f2d8b1 │ OAuth Implementation Discussion        │ chatgpt  │ 2025-02-10 │ 12   │
│ b7c9e4f2 │ Python Async Best Practices            │ chatgpt  │ 2025-02-08 │ 8    │
└──────────┴────────────────────────────────────────┴──────────┴────────────┴──────┘
Showing 2 of 150 conversations
```

### Logic
1. Initialize VaultDB from vault_path
2. Call `db.list_conversations(limit=limit, offset=offset, source=source)`
3. Call `db.count_conversations()` for total
4. Build Rich Table with columns: ID (first 8 chars), Title (truncated to 40 chars), Source, Date (YYYY-MM-DD from created_at), Msgs (message_count)
5. Print table
6. Print `f"Showing {len(conversations)} of {total} conversations"`
7. If no conversations, print "No conversations found. Import some with: vault import chatgpt <file>"

### Error Handling
- If vault not initialized (db file doesn't exist), print error and suggest `vault init`

## Conventions
- Google-style docstrings
- Use `from rich.table import Table` and `from rich.console import Console`
- Match the existing code style in main.py

---

## Console Prompt

```
Read vault/cli/main.py to see the existing CLI commands and code style. Read vault/storage/db.py to see the VaultDB API. Then ADD a new "list" command to the existing main.py that shows conversations in a Rich table. Columns: ID (first 8 chars), Title (truncated 40 chars), Source, Date (YYYY-MM-DD), Msgs. Options: --limit (default 20), --offset, --source filter. Show total count at bottom. Handle the case where vault is not initialized. Do NOT overwrite existing commands.
```
