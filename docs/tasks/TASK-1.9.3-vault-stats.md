# Task 1.9.3: vault stats Command

**Target file:** `vault/cli/main.py` (add to existing)
**Recommended model:** Qwen2.5-Coder or GitHub Copilot
**Effort:** Small (~30 min)
**Dependencies:** `vault/storage/db.py` and `vault/storage/blobs.py` must exist

---

## Context

The vault CLI needs a `stats` command that shows a dashboard of vault metrics. The `VaultDB` class provides count and aggregation methods, and `BlobStore` provides storage size.

**IMPORTANT:** By the time you work on this, `vault/cli/main.py` will have multiple existing commands. You are ADDING a new command — do NOT overwrite the file.

## Files to Read First
- `vault/cli/main.py` — existing CLI
- `vault/storage/db.py` — VaultDB methods (count_conversations, count_messages, get_source_counts, get_date_range)
- `vault/storage/blobs.py` — BlobStore.get_total_size()

## Requirements

Add a `stats` command:

```python
@app.command()
def stats(
    vault_path: Path = typer.Option(Path("vault_data"), help="Path to vault"),
) -> None:
    """Display vault statistics."""
```

### Display Format
Use Rich Panel and Table:
```
╭─── Vault Statistics ────────────────────────╮
│                                             │
│  Total Conversations:  150                  │
│  Total Messages:       3,245                │
│  Encrypted Storage:    45.2 MB              │
│                                             │
│  Sources:                                   │
│    chatgpt:  120                            │
│    claude:   30                              │
│                                             │
│  Date Range:                                │
│    Oldest:  2024-01-15                      │
│    Newest:  2025-02-16                      │
╰─────────────────────────────────────────────╯
```

### Logic
1. Initialize VaultDB and BlobStore from vault_path
2. Query: `db.count_conversations()`, `db.count_messages()`, `db.get_source_counts()`, `db.get_date_range()`
3. Get storage size: `blob_store.get_total_size()` (convert bytes to human-readable MB/GB)
4. Format and display with Rich

### Edge Cases
- Empty vault (0 conversations) — show zeros, "No conversations yet"
- Vault not initialized — error message with `vault init` suggestion

## Conventions
- Google-style docstrings
- Use Rich Console, Panel, Table
- Match existing code style in main.py
- Format numbers with commas (e.g., "3,245")
- Format bytes as MB/GB (e.g., "45.2 MB")

---

## Console Prompt

```
Read vault/cli/main.py, vault/storage/db.py, and vault/storage/blobs.py. Then ADD a "stats" command to the existing main.py that displays vault statistics in a Rich Panel. Show: total conversations, total messages, encrypted storage size (human-readable MB/GB), source breakdown, and date range (oldest/newest). Handle empty vault and uninitialized vault cases. Format numbers with commas. Do NOT overwrite existing commands.
```
