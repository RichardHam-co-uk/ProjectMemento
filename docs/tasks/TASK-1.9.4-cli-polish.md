# Task 1.9.4: CLI Error Handling & Help Text Polish

**Target file:** `vault/cli/main.py` (edit existing)
**Recommended model:** Claude Haiku 4.5 or GPT-4o-mini
**Effort:** Small (~1.5 hours)
**Dependencies:** All CLI commands must already exist (Tasks 1.4.2, 1.9.1, 1.9.2, 1.9.3)

---

## Context

All CLI commands exist but use minimal error handling — most just let Python
exceptions bubble up with raw tracebacks. This task wraps every command body
in consistent try/except blocks, adds actionable error messages, and fills in
rich `--help` epilogs.

**IMPORTANT:** Read `vault/cli/main.py` first. You are **editing** it — do NOT
overwrite or remove any existing commands.

## Files to Read First

- `vault/cli/main.py` — full file

## Requirements

### 1. Wrap each command in try/except

Every command function body should be wrapped in a top-level
`try … except Exception as exc` block:

```python
try:
    # existing command logic
except typer.Exit:
    raise  # always re-raise Exit so exit codes propagate
except Exception as exc:
    console.print(f"[red]Error:[/red] {exc}")
    raise typer.Exit(code=1)
```

Place the `except typer.Exit: raise` clause **before** the general
`except Exception` clause.

### 2. Specific error messages for common cases

Add these user-friendly checks **before** the generic except:

| Situation | Message |
|-----------|---------|
| `db_file` does not exist | `"Vault not initialised. Run vault init first."` |
| `FileNotFoundError` on import file | `"File not found: {path}"` |
| `ValueError` from adapter | `"Invalid file format: {exc}"` |
| Passphrase too short in `init` | `"Passphrase must be at least 12 characters."` |
| Vault already exists in `init` | `"Vault already exists at {path}. Nothing to do."` |

Most of these already exist — just make sure they're all using `[red]…[/red]`
Rich markup and exit with code 1.

### 3. Add `epilog` to the Typer app

```python
app = typer.Typer(
    help="LLM Memory Vault — manage your local encrypted conversation store.",
    epilog="Run 'vault <command> --help' for command-specific help.",
)
```

### 4. Add examples to each command's docstring

Typer renders the docstring as help text. Append an `Examples:` block to
each command's docstring:

**init:**
```
Examples:
    vault init
    vault init --vault-path ~/my_vault --timeout 60
```

**lock:**
```
Examples:
    vault lock
    vault lock --vault-path ~/my_vault
```

**list:**
```
Examples:
    vault list
    vault list --limit 50 --source chatgpt
    vault list --offset 20
```

**show:**
```
Examples:
    vault show a3f2d8b1
    vault show a3f2d8b1cafe1234567890abcdef1234567890abcdef1234567890abcdef12
    vault show a3f2d8b1 --max-messages 50
```

**stats:**
```
Examples:
    vault stats
    vault stats --vault-path ~/my_vault
```

**import chatgpt:**
```
Examples:
    vault import chatgpt ~/Downloads/conversations.json
    vault import chatgpt ./export.json --vault-path ~/my_vault
```

### 5. Consistent exit codes

| Situation | Exit code |
|-----------|-----------|
| Success | 0 |
| Vault not initialised | 1 |
| File not found | 1 |
| Invalid format | 1 |
| Passphrase error | 1 |
| Unexpected exception | 1 |

All `raise typer.Exit(code=N)` calls should already use code 1 for errors.
Audit the file and make sure no error path exits with code 0.

## Conventions

- Keep all changes within `vault/cli/main.py`.
- Do not add new imports beyond `typer` and `rich.console.Console` (both
  already imported).
- Google-style docstrings, match existing file style.

---

## Console Prompt

```
Read vault/cli/main.py in full. Then make these targeted edits:

1. Add epilog to the Typer() constructor: "Run 'vault <command> --help' for
   command-specific help."
2. Wrap every command body in try/except — re-raise typer.Exit, catch
   Exception and print "[red]Error:[/red] {exc}" then raise typer.Exit(code=1).
3. Append an Examples: block to the docstring of each command (init, lock,
   list, show, stats, import chatgpt).
4. Audit all raise typer.Exit() calls — any error path must use code=1.

Do NOT remove or restructure any existing commands. Make the smallest
changes possible to satisfy the requirements.
```
