"""Vault CLI entry point.

Provides the ``vault`` command group with sub-commands for managing and
querying the LLM Memory Vault.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
app = typer.Typer()

# Sub-application for `vault import <provider> <file>`
import_app = typer.Typer(help="Import conversations from a provider export.")
app.add_typer(import_app, name="import")


@app.command()
def version() -> None:
    """Print the version of the Vault CLI."""
    typer.echo("LLM Memory Vault v0.1.0")


@app.command()
def init(
    vault_path: Path = typer.Option(Path("vault_data"), help="Path to vault"),
    timeout: int = typer.Option(30, help="Session timeout in minutes"),
) -> None:
    """Initialise a new vault and start an authenticated session.

    Creates the vault directory structure, initialises the database schema,
    derives a master key from your passphrase, and writes a time-limited
    session token so subsequent commands don't ask for the passphrase again.
    """
    # ---- directory structure ------------------------------------------------
    vault_path = vault_path.resolve()
    if vault_path.exists() and (vault_path / "vault.db").exists():
        console.print(
            f"[yellow]Vault already exists at [bold]{vault_path}[/bold].[/yellow] "
            "Nothing to do."
        )
        raise typer.Exit(code=0)

    vault_path.mkdir(parents=True, exist_ok=True)
    (vault_path / "blobs").mkdir(exist_ok=True)

    # ---- database -----------------------------------------------------------
    from vault.storage.db import VaultDB

    db = VaultDB(vault_path / "vault.db")
    db.init_schema()

    # ---- passphrase & key derivation ----------------------------------------
    from vault.security.crypto import KeyManager

    passphrase: str = typer.prompt(
        "Choose a passphrase (min 12 characters)",
        hide_input=True,
        confirmation_prompt=True,
    )
    if len(passphrase) < 12:
        console.print("[red]Passphrase must be at least 12 characters.[/red]")
        raise typer.Exit(code=1)

    key_mgr = KeyManager(vault_path)
    try:
        master_key = key_mgr.derive_master_key(passphrase)
    except Exception as exc:
        console.print(f"[red]Key derivation failed:[/red] {exc}")
        raise typer.Exit(code=1)

    # ---- session token ------------------------------------------------------
    from vault.security.session import SessionManager

    session_mgr = SessionManager(vault_path, timeout_minutes=timeout)
    token = session_mgr.create_session(master_key)

    # ---- done ---------------------------------------------------------------
    console.print(
        Panel(
            f"  Vault created at: [bold]{vault_path}[/bold]\n"
            f"  Session expires in: [bold]{timeout} minutes[/bold]\n\n"
            "  To authenticate in a new shell, set:\n"
            f"    [bold cyan]export VAULT_TOKEN={token}[/bold cyan]\n"
            f"    [bold cyan]export VAULT_PATH={vault_path}[/bold cyan]",
            title="[green]Vault Initialised[/green]",
            expand=False,
        )
    )


@app.command()
def lock(
    vault_path: Path = typer.Option(Path("vault_data"), help="Path to vault"),
) -> None:
    """Lock the vault by destroying the current session token.

    The on-disk session file is overwritten with random bytes before deletion
    so the encrypted master key cannot be recovered from disk.
    """
    from vault.security.session import SessionManager

    vault_path = vault_path.resolve()
    session_mgr = SessionManager(vault_path)

    if not session_mgr.is_active():
        console.print("[dim]No active session found — vault is already locked.[/dim]")
        raise typer.Exit(code=0)

    session_mgr.clear_session()
    console.print("[green]Vault locked.[/green] Session token destroyed.")


@app.command("list")
def list_conversations(
    limit: int = typer.Option(20, help="Number of conversations to show"),
    offset: int = typer.Option(0, help="Skip N conversations"),
    source: Optional[str] = typer.Option(None, help="Filter by source (e.g., 'chatgpt')"),
    vault_path: Path = typer.Option(Path("vault_data"), help="Path to vault"),
) -> None:
    """List conversations stored in the vault."""
    db_file = vault_path / "vault.db"
    if not db_file.exists():
        console.print(
            "[red]Vault not initialised.[/red] "
            f"Expected database at [bold]{db_file}[/bold].\n"
            "Run [bold]vault init[/bold] to create a new vault."
        )
        raise typer.Exit(code=1)

    from vault.storage.db import VaultDB

    db = VaultDB(db_file)
    conversations = db.list_conversations(limit=limit, offset=offset, source=source)
    total = db.count_conversations()

    if not conversations:
        console.print(
            "No conversations found. Import some with: "
            "[bold]vault import chatgpt <file>[/bold]"
        )
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Title", max_width=40)
    table.add_column("Source", width=10)
    table.add_column("Date", width=12)
    table.add_column("Msgs", justify="right", width=6)

    for conv in conversations:
        short_id = conv.id[:8]
        title = conv.title[:40] if len(conv.title) <= 40 else conv.title[:37] + "..."
        date_str = conv.created_at.strftime("%Y-%m-%d") if conv.created_at else "—"
        table.add_row(short_id, title, conv.source, date_str, str(conv.message_count))

    console.print(table)
    console.print(f"Showing [bold]{len(conversations)}[/bold] of [bold]{total}[/bold] conversations")


@app.command()
def stats(
    vault_path: Path = typer.Option(Path("vault_data"), help="Path to vault"),
) -> None:
    """Display vault statistics."""
    db_file = vault_path / "vault.db"
    if not db_file.exists():
        console.print(
            "[red]Vault not initialised.[/red] "
            f"Expected database at [bold]{db_file}[/bold].\n"
            "Run [bold]vault init[/bold] to create a new vault."
        )
        raise typer.Exit(code=1)

    from vault.storage.db import VaultDB

    db = VaultDB(db_file)

    conv_count = db.count_conversations()
    msg_count = db.count_messages()
    source_counts = db.get_source_counts()
    oldest, newest = db.get_date_range()

    # Compute blob storage size by walking the directory directly so that
    # the stats command has no crypto dependency at import time.
    blob_root = vault_path / "blobs"
    total_bytes = (
        sum(f.stat().st_size for f in blob_root.rglob("*.enc"))
        if blob_root.exists()
        else 0
    )

    def _fmt_bytes(n: int) -> str:
        if n >= 1_073_741_824:
            return f"{n / 1_073_741_824:.1f} GB"
        if n >= 1_048_576:
            return f"{n / 1_048_576:.1f} MB"
        if n >= 1_024:
            return f"{n / 1_024:.1f} KB"
        return f"{n} B"

    lines: list[str] = []
    lines.append(f"  Total Conversations:  [bold]{conv_count:,}[/bold]")
    lines.append(f"  Total Messages:       [bold]{msg_count:,}[/bold]")
    lines.append(f"  Encrypted Storage:    [bold]{_fmt_bytes(total_bytes)}[/bold]")
    lines.append("")

    if source_counts:
        lines.append("  Sources:")
        for src, count in sorted(source_counts.items()):
            lines.append(f"    {src}:  {count:,}")
    else:
        lines.append("  Sources:  [dim]No conversations yet[/dim]")

    lines.append("")

    if oldest and newest:
        lines.append("  Date Range:")
        lines.append(f"    Oldest:  {oldest.strftime('%Y-%m-%d')}")
        lines.append(f"    Newest:  {newest.strftime('%Y-%m-%d')}")
    else:
        lines.append("  Date Range:  [dim]No conversations yet[/dim]")

    console.print(Panel("\n".join(lines), title="Vault Statistics", expand=False))


@import_app.command("chatgpt")
def import_chatgpt(
    file: Path = typer.Argument(..., help="Path to conversations.json from ChatGPT export"),
    vault_path: Path = typer.Option(Path("vault_data"), help="Path to vault"),
) -> None:
    """Import conversations from a ChatGPT data export.

    Expects the ``conversations.json`` file produced by ChatGPT's
    Settings → Data Controls → Export Data feature.  Conversations already
    present in the vault are silently skipped (idempotent).
    """
    vault_path = vault_path.resolve()
    db_file = vault_path / "vault.db"
    if not db_file.exists():
        console.print(
            "[red]Vault not initialised.[/red] "
            f"Expected database at [bold]{db_file}[/bold].\n"
            "Run [bold]vault init[/bold] to create a new vault."
        )
        raise typer.Exit(code=1)

    if not file.exists():
        console.print(f"[red]File not found:[/red] {file}")
        raise typer.Exit(code=1)

    from vault.ingestion.chatgpt import ChatGPTAdapter, run_import
    from vault.storage.db import VaultDB

    if not ChatGPTAdapter().validate_format(file):
        console.print(
            f"[red]File does not look like a ChatGPT export:[/red] {file}\n"
            "Expected a JSON array with 'mapping' and 'create_time' fields."
        )
        raise typer.Exit(code=1)

    db = VaultDB(db_file)

    with console.status("[bold cyan]Importing conversations…[/bold cyan]"):
        result = run_import(file_path=file, db=db)

    # Summary panel
    lines = [
        f"  Imported:  [bold green]{result.imported}[/bold green]",
        f"  Skipped:   [bold yellow]{result.skipped}[/bold yellow]  (already in vault)",
        f"  Failed:    [bold red]{result.failed}[/bold red]",
    ]
    if result.errors:
        lines.append("")
        lines.append("  Errors:")
        for err in result.errors[:5]:
            lines.append(f"    [red]•[/red] {err}")
        if len(result.errors) > 5:
            lines.append(f"    … and {len(result.errors) - 5} more")

    console.print(Panel("\n".join(lines), title="Import Complete", expand=False))

    if result.failed > 0 and result.imported == 0:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
