"""
LLM Memory Vault CLI entry point.

Provides the `vault` command group with sub-commands for managing
the encrypted local knowledge base.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from vault.security.crypto import KeyManager
from vault.storage.database import VaultDB

app = typer.Typer(
    name="vault",
    help="LLM Memory Vault — local-first AI conversation store.",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True, style="bold red")

_MIN_PASSPHRASE_LEN = 12
_SESSION_TOKEN_ENV = "VAULT_SESSION_TOKEN"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _prompt_passphrase(confirm: bool = True) -> str:
    """Prompt for a passphrase (hidden input), optionally with confirmation.

    Args:
        confirm: If True, ask the user to type the passphrase twice.

    Returns:
        The passphrase string.

    Raises:
        typer.Exit: If the passphrase is too short or confirmation fails.
    """
    passphrase = typer.prompt("Enter master passphrase", hide_input=True)

    if len(passphrase) < _MIN_PASSPHRASE_LEN:
        err_console.print(
            f"[red]Passphrase too short.[/] "
            f"Minimum {_MIN_PASSPHRASE_LEN} characters required "
            f"(got {len(passphrase)})."
        )
        raise typer.Exit(code=1)

    if confirm:
        passphrase2 = typer.prompt("Confirm passphrase", hide_input=True)
        if passphrase != passphrase2:
            err_console.print("[red]Passphrases do not match.[/] Aborting.")
            raise typer.Exit(code=1)

    return passphrase


def _passphrase_strength(passphrase: str) -> str:
    """Return a simple strength label ('WEAK', 'MODERATE', or 'STRONG').

    Args:
        passphrase: The passphrase to evaluate.

    Returns:
        Strength label string.
    """
    length = len(passphrase)
    variety = sum([
        any(c.isupper() for c in passphrase),
        any(c.islower() for c in passphrase),
        any(c.isdigit() for c in passphrase),
        any(not c.isalnum() for c in passphrase),
    ])
    if length >= 20 and variety >= 3:
        return "STRONG"
    if length >= 16 and variety >= 2:
        return "MODERATE"
    return "WEAK"


def _get_master_key(vault_path: Path) -> bytes:
    """Return the master key, using session token or prompting for passphrase.

    Checks for a valid session token in the VAULT_SESSION_TOKEN environment
    variable first. If found and valid, returns the cached master key. Otherwise,
    prompts for the passphrase, derives the key, and creates a new session.

    Args:
        vault_path: Path to the vault root directory.

    Returns:
        The 32-byte master key.

    Raises:
        typer.Exit: If the vault does not exist or authentication fails.
    """
    from vault.security.session import SessionManager

    salt_file = vault_path / ".salt"
    if not salt_file.exists():
        err_console.print(
            f"[red]No vault found at[/] [bold]{vault_path}[/].\n"
            "Run [bold]vault init[/] to create one."
        )
        raise typer.Exit(code=1)

    sm = SessionManager(vault_path)
    token = os.environ.get(_SESSION_TOKEN_ENV)

    if token:
        master_key = sm.validate_token(token)
        if master_key:
            return master_key
        console.print("[yellow]Session expired — please re-authenticate.[/]")

    # Prompt for passphrase
    passphrase = typer.prompt("Enter master passphrase", hide_input=True)
    if len(passphrase) < _MIN_PASSPHRASE_LEN:
        err_console.print("[red]Invalid passphrase.[/]")
        raise typer.Exit(code=1)

    try:
        km = KeyManager(vault_path)
        master_key = km.derive_master_key(passphrase)
    except (ValueError, OSError) as exc:
        err_console.print(f"[red]Authentication failed:[/] {exc}")
        raise typer.Exit(code=1)
    finally:
        del passphrase

    # Cache session for subsequent commands
    new_token = sm.create_session(master_key)
    os.environ[_SESSION_TOKEN_ENV] = new_token

    return master_key


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Print the version of the Vault CLI."""
    console.print("LLM Memory Vault [bold cyan]v0.1.0[/]")


@app.command()
def init(
    vault_path: Path = typer.Option(
        Path("vault_data"),
        "--vault-path",
        "-p",
        help="Directory where vault data will be stored.",
        show_default=True,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite an existing vault (destructive!).",
    ),
) -> None:
    """Initialize a new LLM Memory Vault.

    Creates the vault directory structure, derives and stores the
    encryption salt, and initialises the SQLite database schema.

    \b
    Directory layout created:
        vault_path/
        ├── .salt          — 16-byte random Argon2 salt
        ├── vault.db       — SQLite conversation database
        └── blobs/         — Encrypted message content

    \b
    Security note:
        Your passphrase is the ONLY way to decrypt your vault.
        Store it in a password manager — it cannot be recovered.
    """
    console.print(
        Panel.fit(
            "[bold cyan]Initialize LLM Memory Vault[/]",
            border_style="cyan",
        )
    )

    # ------------------------------------------------------------------
    # Guard: existing vault
    # ------------------------------------------------------------------
    salt_file = vault_path / ".salt"
    db_file = vault_path / "vault.db"

    if vault_path.exists() and (salt_file.exists() or db_file.exists()):
        if not force:
            err_console.print(
                f"[red]Vault already exists[/] at [bold]{vault_path}[/].\n"
                "Use [bold]--force[/] to overwrite "
                "(this will destroy all existing data)."
            )
            raise typer.Exit(code=1)

        console.print(
            "[yellow]⚠  --force specified — overwriting existing vault.[/]"
        )
        if salt_file.exists():
            salt_file.unlink()
        if db_file.exists():
            db_file.unlink()

    # ------------------------------------------------------------------
    # Passphrase
    # ------------------------------------------------------------------
    passphrase = _prompt_passphrase(confirm=True)
    strength = _passphrase_strength(passphrase)
    colour = {"WEAK": "red", "MODERATE": "yellow", "STRONG": "green"}[strength]
    console.print(f"  Passphrase strength: [{colour}]{strength}[/]")
    if strength == "WEAK":
        console.print(
            "  [yellow]Tip:[/] Use 20+ characters with mixed case, "
            "digits, and symbols."
        )

    # ------------------------------------------------------------------
    # Initialise vault
    # ------------------------------------------------------------------
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Creating vault directories…", total=None)

        # 1. Create directory layout
        try:
            vault_path.mkdir(parents=True, exist_ok=True)
            (vault_path / "blobs").mkdir(exist_ok=True)
        except OSError as exc:
            progress.stop()
            err_console.print(f"[red]Failed to create directories:[/] {exc}")
            raise typer.Exit(code=1)

        # 2. Derive master key (generates and persists .salt)
        progress.update(task, description="Deriving encryption key (Argon2id)…")
        try:
            key_manager = KeyManager(vault_path)
            master_key = key_manager.derive_master_key(passphrase)
        except (ValueError, OSError) as exc:
            progress.stop()
            err_console.print(f"[red]Key derivation failed:[/] {exc}")
            raise typer.Exit(code=1)

        # 3. Initialise database schema
        progress.update(task, description="Initialising database schema…")
        try:
            db = VaultDB(vault_path / "vault.db")
            db.create_schema()
        except Exception as exc:
            progress.stop()
            err_console.print(f"[red]Database initialisation failed:[/] {exc}")
            raise typer.Exit(code=1)

        progress.update(task, description="Done.")

    # ------------------------------------------------------------------
    # Success output
    # ------------------------------------------------------------------
    console.print()
    console.print("[green]✓[/] Vault directory created")
    console.print("[green]✓[/] Encryption initialised (Argon2id + Fernet)")
    console.print("[green]✓[/] Database schema created")
    console.print()
    console.print(
        Panel(
            f"[bold green]Vault initialised at:[/] {vault_path.resolve()}\n\n"
            "[bold yellow]⚠  CRITICAL — store your passphrase securely![/]\n"
            "   Without it, your vault [bold]cannot[/] be recovered.\n"
            "   Use a password manager (Bitwarden, 1Password, etc.).",
            title="Success",
            border_style="green",
        )
    )
    console.print()
    console.print("[bold]Next steps:[/]")
    console.print("  1. [cyan]vault import chatgpt <export.json>[/]")
    console.print("  2. [cyan]vault list[/]")
    console.print()

    # Best-effort zero-out of sensitive values in CPython
    del master_key
    del passphrase


@app.command()
def lock(
    vault_path: Path = typer.Option(
        Path("vault_data"),
        "--vault-path",
        "-p",
        help="Path to the vault directory.",
    ),
) -> None:
    """Lock the vault by clearing the active session token.

    After locking, the next command will prompt for the passphrase again.
    """
    from vault.security.session import SessionManager

    sm = SessionManager(vault_path)
    if sm.is_active():
        sm.clear_session()
        os.environ.pop(_SESSION_TOKEN_ENV, None)
        console.print("[green]✓[/] Vault locked — session cleared.")
    else:
        console.print("[yellow]No active session found.[/]")


@app.command(name="import")
def import_conversations(
    provider: str = typer.Argument(
        ...,
        help="Provider name (chatgpt, claude, perplexity, ollama).",
    ),
    file_path: Path = typer.Argument(
        ...,
        help="Path to the provider export file.",
        exists=True,
        readable=True,
    ),
    vault_path: Path = typer.Option(
        Path("vault_data"),
        "--vault-path",
        "-p",
        help="Path to the vault directory.",
        show_default=True,
    ),
) -> None:
    """Import conversations from an LLM provider export file.

    \b
    Supported providers:
        chatgpt   — OpenAI ChatGPT JSON export (conversations.json)

    \b
    Example:
        vault import chatgpt ~/Downloads/conversations.json
    """
    from vault.ingestion.chatgpt import ChatGPTAdapter
    from vault.ingestion.pipeline import ImportPipeline
    from vault.storage.blobs import BlobStore

    # ------------------------------------------------------------------
    # Resolve adapter
    # ------------------------------------------------------------------
    _adapters = {"chatgpt": ChatGPTAdapter}
    if provider.lower() not in _adapters:
        err_console.print(
            f"[red]Unknown provider:[/] [bold]{provider}[/]\n"
            f"Supported: {', '.join(_adapters)}"
        )
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # Authenticate
    # ------------------------------------------------------------------
    master_key = _get_master_key(vault_path)

    # ------------------------------------------------------------------
    # Set up pipeline
    # ------------------------------------------------------------------
    try:
        key_manager = KeyManager(vault_path)
        key_manager.cache_master_key(master_key)
        blob_store = BlobStore(vault_path / "blobs", key_manager)
        db = VaultDB(vault_path / "vault.db")
        db.create_schema()  # no-op if already exists

        adapter = _adapters[provider.lower()]()
        pipeline = ImportPipeline(db, blob_store, key_manager)
    except Exception as exc:
        err_console.print(f"[red]Failed to initialise import pipeline:[/] {exc}")
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # Validate file format
    # ------------------------------------------------------------------
    if not adapter.validate_format(file_path):
        err_console.print(
            f"[red]File does not appear to be a valid {provider} export:[/]\n"
            f"  {file_path}"
        )
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # Run import with progress display
    # ------------------------------------------------------------------
    console.print(f"\nImporting from [bold cyan]{provider}[/]…\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        prog_task = progress.add_task(f"Processing {file_path.name}", total=None)

        def _on_progress(current: int, total: int) -> None:
            progress.update(
                prog_task,
                completed=current,
                total=total,
                description=f"Processing conversations",
            )

        try:
            result = pipeline.import_conversations(
                adapter, file_path, master_key, progress_callback=_on_progress
            )
        except Exception as exc:
            progress.stop()
            err_console.print(f"[red]Import failed:[/] {exc}")
            raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # Summary table
    # ------------------------------------------------------------------
    console.print()
    table = Table(show_header=True, header_style="bold")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("[green]Imported[/]", str(result.imported))
    table.add_row("[yellow]Skipped (duplicates)[/]", str(result.skipped))
    table.add_row("[red]Failed[/]", str(result.failed))
    console.print(table)
    console.print()

    if result.imported:
        console.print(
            f"[green]✓[/] Import complete! "
            f"[bold]{result.imported}[/] conversation(s) added to vault."
        )
        console.print("\nNext: [cyan]vault list[/]")
    else:
        console.print("[yellow]No new conversations imported.[/]")

    if result.errors:
        console.print(f"\n[yellow]Warnings ({len(result.errors)}):[/]")
        for title, msg in result.errors[:5]:
            console.print(f"  • {title}: {msg}")
        if len(result.errors) > 5:
            console.print(f"  … and {len(result.errors) - 5} more.")


@app.command(name="list")
def list_conversations(
    limit: int = typer.Option(
        20, "--limit", "-n", help="Number of conversations to show.", show_default=True
    ),
    offset: int = typer.Option(
        0, "--offset", help="Skip N conversations (for pagination).", show_default=True
    ),
    source: Optional[str] = typer.Option(
        None, "--source", "-s", help="Filter by provider (e.g. chatgpt)."
    ),
    vault_path: Path = typer.Option(
        Path("vault_data"),
        "--vault-path",
        "-p",
        help="Path to the vault directory.",
        show_default=True,
    ),
) -> None:
    """List conversations stored in the vault.

    \b
    Examples:
        vault list
        vault list --limit 50
        vault list --source chatgpt
        vault list --offset 20
    """
    # Auth required to confirm vault is accessible; we don't decrypt here.
    _get_master_key(vault_path)

    try:
        db = VaultDB(vault_path / "vault.db")
        conversations = db.list_conversations(limit=limit, offset=offset, source=source)
        total = db.get_conversation_count()
    except Exception as exc:
        err_console.print(f"[red]Failed to read vault:[/] {exc}")
        raise typer.Exit(code=1)

    if not conversations:
        console.print("[yellow]No conversations found.[/]")
        if source:
            console.print(f"  Filter active: source=[bold]{source}[/]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID (first 8)", style="dim", no_wrap=True)
    table.add_column("Title", max_width=45)
    table.add_column("Source", justify="center")
    table.add_column("Date", justify="right")
    table.add_column("Msgs", justify="right")

    for conv in conversations:
        date_str = conv.created_at.strftime("%Y-%m-%d") if conv.created_at else "—"
        table.add_row(
            conv.id[:8],
            conv.title or "(untitled)",
            conv.source,
            date_str,
            str(conv.message_count),
        )

    console.print()
    console.print(table)
    console.print(
        f"\nShowing [bold]{len(conversations)}[/] of [bold]{total}[/] conversation(s)"
        + (f" (source: {source})" if source else "")
        + (f" — use [cyan]--offset {offset + limit}[/] for next page" if offset + limit < total else "")
    )


@app.command()
def show(
    conversation_id: str = typer.Argument(
        ...,
        help="Conversation ID (or unique prefix of the ID).",
    ),
    view: str = typer.Option(
        "raw",
        "--view",
        "-v",
        help="Display mode: raw (full content) or meta (metadata only).",
    ),
    max_messages: int = typer.Option(
        100,
        "--max-messages",
        "-m",
        help="Maximum number of messages to display.",
        show_default=True,
    ),
    vault_path: Path = typer.Option(
        Path("vault_data"),
        "--vault-path",
        "-p",
        help="Path to the vault directory.",
        show_default=True,
    ),
) -> None:
    """Display a conversation from the vault.

    Use `vault list` to find conversation IDs. You can pass just the first
    few characters of an ID — the vault will find a unique match.

    \b
    Examples:
        vault show a1b2c3d4
        vault show a1b2c3d4 --view meta
        vault show a1b2c3d4 --max-messages 20
    """
    from vault.storage.blobs import BlobStore

    master_key = _get_master_key(vault_path)

    try:
        db = VaultDB(vault_path / "vault.db")
        key_manager = KeyManager(vault_path)
        key_manager.cache_master_key(master_key)
        blob_store = BlobStore(vault_path / "blobs", key_manager)
    except Exception as exc:
        err_console.print(f"[red]Failed to open vault:[/] {exc}")
        raise typer.Exit(code=1)

    # Support prefix matching
    conv = db.get_conversation(conversation_id)
    if conv is None:
        # Try prefix match
        all_convs = db.list_conversations(limit=1000)
        matches = [c for c in all_convs if c.id.startswith(conversation_id)]
        if len(matches) == 1:
            conv = matches[0]
        elif len(matches) > 1:
            err_console.print(
                f"[red]Ambiguous ID prefix[/] '[bold]{conversation_id}[/]' "
                f"matches {len(matches)} conversations. Use more characters."
            )
            raise typer.Exit(code=1)
        else:
            err_console.print(
                f"[red]Conversation not found:[/] [bold]{conversation_id}[/]"
            )
            raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # Metadata header
    # ------------------------------------------------------------------
    date_str = conv.created_at.strftime("%Y-%m-%d %H:%M UTC") if conv.created_at else "unknown"
    console.print()
    console.print(
        Panel(
            f"[bold]{conv.title or '(untitled)'}[/]\n"
            f"[dim]ID:[/]      {conv.id}\n"
            f"[dim]Source:[/]  {conv.source}\n"
            f"[dim]Date:[/]    {date_str}\n"
            f"[dim]Messages:[/] {conv.message_count}  "
            f"[dim]Sensitivity:[/] {conv.sensitivity.value}",
            border_style="cyan",
        )
    )

    if view == "meta":
        return

    # ------------------------------------------------------------------
    # Decrypt and display messages
    # ------------------------------------------------------------------
    messages = db.get_messages(conv.id)
    if not messages:
        console.print("[yellow]No messages found for this conversation.[/]")
        return

    displayed = messages[:max_messages]
    if len(messages) > max_messages:
        console.print(
            f"[yellow]Showing first {max_messages} of {len(messages)} messages.[/]\n"
        )

    actor_style = {
        "user": "[bold blue]USER[/]",
        "assistant": "[bold green]ASSISTANT[/]",
        "system": "[dim]SYSTEM[/]",
    }

    for msg in displayed:
        ts = msg.timestamp.strftime("%Y-%m-%d %H:%M") if msg.timestamp else ""
        actor_label = actor_style.get(msg.actor.value, msg.actor.value.upper())

        try:
            content_bytes = blob_store.retrieve(msg.content_blob_uuid, master_key, conv.id)
            content = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            content = "[dim italic](content unavailable)[/]"

        console.rule(f"{actor_label}  [dim]{ts}[/]")
        console.print(content)
        console.print()

    if len(messages) > max_messages:
        console.print(
            f"[dim]… {len(messages) - max_messages} more messages. "
            f"Use --max-messages to see more.[/]"
        )


@app.command()
def stats(
    vault_path: Path = typer.Option(
        Path("vault_data"),
        "--vault-path",
        "-p",
        help="Path to the vault directory.",
        show_default=True,
    ),
) -> None:
    """Display vault statistics and usage summary."""
    _get_master_key(vault_path)

    try:
        db = VaultDB(vault_path / "vault.db")
        conv_count = db.get_conversation_count()
        msg_count = db.get_message_count()
        source_breakdown = db.get_source_breakdown()
        oldest, newest = db.get_date_range()
    except Exception as exc:
        err_console.print(f"[red]Failed to read vault stats:[/] {exc}")
        raise typer.Exit(code=1)

    # Blob storage size
    blob_dir = vault_path / "blobs"
    blob_size_bytes = sum(
        f.stat().st_size for f in blob_dir.rglob("*.enc") if f.is_file()
    ) if blob_dir.exists() else 0
    blob_size_mb = blob_size_bytes / (1024 * 1024)

    console.print()
    console.print(
        Panel.fit("[bold cyan]Vault Statistics[/]", border_style="cyan")
    )
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Total Conversations", f"{conv_count:,}")
    table.add_row("Total Messages", f"{msg_count:,}")
    table.add_row("Encrypted Storage", f"{blob_size_mb:.1f} MB ({blob_size_bytes:,} bytes)")
    table.add_row(
        "Oldest Conversation",
        oldest.strftime("%Y-%m-%d") if oldest else "—",
    )
    table.add_row(
        "Newest Conversation",
        newest.strftime("%Y-%m-%d") if newest else "—",
    )
    console.print(table)

    if source_breakdown:
        console.print()
        src_table = Table(
            show_header=True,
            header_style="bold",
            title="By Source",
        )
        src_table.add_column("Provider")
        src_table.add_column("Conversations", justify="right")
        src_table.add_column("Share", justify="right")
        for src, count in source_breakdown:
            pct = (count / conv_count * 100) if conv_count else 0
            src_table.add_row(src, str(count), f"{pct:.0f}%")
        console.print(src_table)

    console.print()


if __name__ == "__main__":
    app()
