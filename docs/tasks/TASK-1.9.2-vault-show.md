# Task 1.9.2: vault show Command

**Target file:** `vault/cli/main.py` (add to existing)
**Recommended model:** GPT-4o-mini or Claude Haiku 4.5
**Effort:** Medium (~2 hours)
**Dependencies:** `vault/storage/db.py` (Task 1.4.1)

---

## Context

The vault CLI needs a `show` command that displays the full message thread for a
single conversation. Conversations are identified by their SHA-256 `id`; the CLI
accepts either the full 64-character hash **or** the 8-character short prefix
(e.g. `a3f2d8b1`).

**IMPORTANT:** By the time you work on this task, `vault/cli/main.py` already
contains `version`, `init`, `lock`, `list`, `stats`, and `import chatgpt`
commands. You are **ADDING** a new command — do NOT overwrite the file. Read it
first.

## Files to Read First

- `vault/cli/main.py` — existing CLI (understand code style and patterns)
- `vault/storage/db.py` — `VaultDB` class, especially `get_conversation()` and
  `get_messages_for_conversation()`
- `vault/storage/models.py` — `Conversation` and `Message` ORM models

## Requirements

Add a `show` command to the existing Typer app:

```python
@app.command()
def show(
    conversation_id: str = typer.Argument(..., help="Conversation ID or 8-char prefix"),
    max_messages: int = typer.Option(100, help="Maximum messages to display"),
    vault_path: Path = typer.Option(Path("vault_data"), help="Path to vault"),
) -> None:
    """Display a conversation's messages."""
```

### ID Resolution Logic

The user may supply either the full 64-char ID or the first 8 characters.
Resolve it like this:

1. Try `db.get_conversation(conversation_id)` first (exact match).
2. If `None` **and** `len(conversation_id) == 8`, call
   `db.list_conversations(limit=1000)` and find the first entry whose
   `id.startswith(conversation_id)`. Use that conversation.
3. If still `None`, print an error and exit code 1.

### Display Format

Use Rich panels and styled text:

```
╭─────────────────────────────────────────────────────────╮
│ OAuth Implementation Discussion                         │
│ chatgpt · 2025-02-10  ·  12 messages                   │
╰─────────────────────────────────────────────────────────╯

[USER] 15:30:15
How do I implement OAuth2 with PKCE?

────────────────────────────────────────────────────────────
[ASSISTANT] 15:30:30
OAuth2 with PKCE (Proof Key for Code Exchange) is the
recommended flow for public clients...

────────────────────────────────────────────────────────────
… (showing 2 of 12 messages — use --max-messages to see more)
```

### Logic

1. Initialize `VaultDB` from `vault_path`.
2. Resolve the conversation (exact ID or short prefix — see above).
3. Call `db.get_messages_for_conversation(conv.id)`.
4. Truncate to `max_messages` if needed; show a note if truncated.
5. Print a Rich `Panel` with title = conversation title, subtitle =
   `f"{conv.source} · {date} · {conv.message_count} messages"`.
6. For each message, print:
   - A `[dim]────[/dim]` separator between messages (not before the first).
   - `[bold cyan][USER][/bold cyan]` or `[bold green][ASSISTANT][/bold green]`
     followed by the time (HH:MM:SS from `msg.timestamp`).
   - The message content on the next line (no truncation — full content).
7. If `len(messages) > max_messages`, print a dim note:
   `f"(showing {max_messages} of {len(messages)} messages — use --max-messages N to see more)"`

### Error Handling

- Vault DB not found → print error suggesting `vault init`, exit 1.
- Conversation ID not found → print `"No conversation found with ID: {conversation_id}"`, exit 1.
- No messages → print `"Conversation has no messages."`.

## Conventions

- Google-style docstrings on the command function.
- Match the existing imports and `console = Console()` pattern.
- No new top-level imports beyond what's already in the file; add local
  imports inside the function body where needed.

---

## Console Prompt

```
Read vault/cli/main.py to understand the existing CLI code style. Read
vault/storage/db.py for the VaultDB API. Read vault/storage/models.py
for the Conversation and Message model fields.

Then ADD a "show" command to vault/cli/main.py that accepts a
conversation_id argument (full 64-char hash or 8-char prefix). It should
look up the conversation, retrieve all messages with
get_messages_for_conversation(), and display them using Rich with a Panel
header and coloured [USER]/[ASSISTANT] labels. Handle the short-prefix
ID case: if the exact ID is not found and the input is 8 chars, scan
list_conversations() for a prefix match. Do NOT overwrite existing
commands.
```
