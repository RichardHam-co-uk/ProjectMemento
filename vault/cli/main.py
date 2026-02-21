"""
Vault CLI — command-line interface for the LLM Memory Vault.

Commands:
  version      Print the CLI version.
  init         Initialise a new vault (key derivation + schema setup).
  list         List conversations stored in the vault.
  stats        Show vault statistics.
  import       Import conversations from a provider export file.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

app = typer.Typer(help="LLM Memory Vault — local-first AI memory system.")
console = Console()
err_console = Console(stderr=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ADAPTERS: dict[str, type] = {}


def _get_adapters() -> dict[str, type]:
    """Lazily load and cache available adapters."""
    if not _ADAPTERS:
        from vault.ingestion.chatgpt import ChatGPTAdapter
        _ADAPTERS["chatgpt"] = ChatGPTAdapter
    return _ADAPTERS


def _get_master_key_from_session(vault_path: Path) -> bytes | None:
    """Attempt to retrieve the master key from an active session token.

    Reads VAULT_SESSION_TOKEN from the environment and validates it.

    Args:
        vault_path: Path to the vault root directory.

    Returns:
        32-byte master key if a valid session exists, otherwise None.
    """
    from vault.security.session import SessionManager
    token = os.environ.get("VAULT_SESSION_TOKEN")
    if not token:
        return None
    sm = SessionManager(vault_path)
    return sm.validate_token(token)


def _authenticate(vault_path: Path) -> bytes:
    """Authenticate the user, returning the master key.

    Tries the session token first, then falls back to prompting for the
    passphrase and creating a new session.

    Args:
        vault_path: Path to the vault root directory.

    Returns:
        32-byte master key.

    Raises:
        typer.Exit: If authentication fails.
    """
    from vault.security.crypto import KeyManager
    from vault.security.session import SessionManager

    master_key = _get_master_key_from_session(vault_path)
    if master_key is not None:
        return master_key

    # No valid session — prompt for passphrase
    passphrase = typer.prompt("Vault passphrase", hide_input=True)
    km = KeyManager(vault_path)
    valid, msg = km.validate_passphrase(passphrase)
    if not valid:
        err_console.print(f"[red]Error:[/red] {msg}")
        raise typer.Exit(code=1)

    try:
        master_key = km.derive_master_key(passphrase)
    except Exception as exc:
        err_console.print(f"[red]Error deriving key:[/red] {exc}")
        raise typer.Exit(code=1)

    # Create a session for subsequent commands
    sm = SessionManager(vault_path)
    token = sm.create_session(master_key)
    console.print(
        f"[dim]Session created. To reuse without re-entering your passphrase:[/dim]\n"
        f"  [bold cyan]export VAULT_SESSION_TOKEN={token}[/bold cyan]"
    )
    return master_key


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Print the version of the Vault CLI."""
    typer.echo("LLM Memory Vault v0.1.0")


@app.command()
def init(
    vault_path: Path = typer.Option(
        Path("vault_data"),
        "--vault-path",
        "-p",
        help="Directory where the vault will be created.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite an existing vault (resets salt and database).",
    ),
) -> None:
    """Initialise a new LLM Memory Vault.

    Creates the vault directory, derives a master key from your passphrase,
    initialises the SQLite database schema, and starts a 30-minute session.
    """
    from vault.security.crypto import KeyManager
    from vault.security.session import SessionManager
    from vault.storage.blobs import BlobStore
    from vault.storage.db import VaultDB

    vault_path = vault_path.resolve()
    salt_file = vault_path / ".salt"

    # Guard against accidental overwrites
    if salt_file.exists() and not force:
        err_console.print(
            f"[red]Error:[/red] A vault already exists at [bold]{vault_path}[/bold].\n"
            "Use [bold]--force[/bold] to reinitialise (this will reset the salt and data!)."
        )
        raise typer.Exit(code=1)

    console.print(Panel.fit("[bold cyan]LLM Memory Vault — Initialisation[/bold cyan]"))

    # Collect and validate passphrase (with confirmation)
    km_tmp = KeyManager(vault_path)
    while True:
        passphrase = typer.prompt("Choose a passphrase (min 12 chars)", hide_input=True)
        valid, msg = km_tmp.validate_passphrase(passphrase)
        if not valid:
            console.print(f"[yellow]Warning:[/yellow] {msg}")
            continue
        confirm = typer.prompt("Confirm passphrase", hide_input=True)
        if passphrase != confirm:
            console.print("[yellow]Passphrases do not match. Please try again.[/yellow]")
            continue
        break

    # Create directory structure
    blobs_path = vault_path / "blobs"
    vault_path.mkdir(parents=True, exist_ok=True)
    blobs_path.mkdir(parents=True, exist_ok=True)

    console.print("[dim]Deriving master key (this may take a moment)…[/dim]")

    # Derive master key — writes the .salt file
    km = KeyManager(vault_path)
    try:
        master_key = km.derive_master_key(passphrase)
    except Exception as exc:
        err_console.print(f"[red]Key derivation failed:[/red] {exc}")
        raise typer.Exit(code=1)

    # Initialise the database and run migrations
    db_path = vault_path / "vault.db"
    db = VaultDB(db_path)
    try:
        db.init_schema()
    except Exception as exc:
        err_console.print(f"[red]Database initialisation failed:[/red] {exc}")
        raise typer.Exit(code=1)

    # Initialise blob store (creates directory if needed)
    BlobStore(blobs_path, km)

    # Create a session token
    sm = SessionManager(vault_path)
    token = sm.create_session(master_key)

    # Success output
    console.print()
    console.print(
        Panel(
            f"[bold green]Vault initialised successfully![/bold green]\n\n"
            f"[dim]Location:[/dim]  {vault_path}\n"
            f"[dim]Database:[/dim]  {db_path}\n"
            f"[dim]Blobs:[/dim]     {blobs_path}\n\n"
            "[bold]Next steps:[/bold]\n\n"
            "  1. Export your session token (valid for 30 min):\n"
            f"     [bold cyan]export VAULT_SESSION_TOKEN={token}[/bold cyan]\n\n"
            "  2. Import conversations:\n"
            "     [bold cyan]vault import chatgpt /path/to/conversations.json[/bold cyan]\n\n"
            "  3. Browse conversations:\n"
            "     [bold cyan]vault list[/bold cyan]",
            title="[bold]Vault Ready[/bold]",
            border_style="green",
        )
    )


@app.command("list")
def list_conversations(
    vault_path: Path = typer.Option(
        Path("vault_data"),
        "--vault-path",
        "-p",
        help="Path to the vault directory.",
    ),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum rows to show."),
    source: Optional[str] = typer.Option(
        None, "--source", "-s", help="Filter by provider (e.g. chatgpt)."
    ),
) -> None:
    """List conversations stored in the vault."""
    from vault.storage.db import VaultDB

    vault_path = vault_path.resolve()
    db_path = vault_path / "vault.db"
    if not db_path.exists():
        err_console.print(
            f"[red]No vault found at {vault_path}.[/red] "
            "Run [bold]vault init[/bold] first."
        )
        raise typer.Exit(code=1)

    db = VaultDB(db_path)
    conversations = db.list_conversations(limit=limit, source=source)

    if not conversations:
        console.print("[dim]No conversations found.[/dim]")
        return

    table = Table(
        title=f"Conversations ({len(conversations)} shown)",
        show_lines=False,
    )
    table.add_column("Source", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Messages", justify="right", style="green")
    table.add_column("Created", style="dim")

    for conv in conversations:
        table.add_row(
            conv.source,
            conv.title[:60] + ("…" if len(conv.title) > 60 else ""),
            str(conv.message_count),
            conv.created_at.strftime("%Y-%m-%d") if conv.created_at else "—",
        )

    console.print(table)


@app.command()
def stats(
    vault_path: Path = typer.Option(
        Path("vault_data"),
        "--vault-path",
        "-p",
        help="Path to the vault directory.",
    ),
) -> None:
    """Show statistics about the vault contents."""
    from vault.storage.db import VaultDB

    vault_path = vault_path.resolve()
    db_path = vault_path / "vault.db"
    if not db_path.exists():
        err_console.print(
            f"[red]No vault found at {vault_path}.[/red] "
            "Run [bold]vault init[/bold] first."
        )
        raise typer.Exit(code=1)

    db = VaultDB(db_path)
    total_convs = db.count_conversations()
    total_msgs = db.count_messages()
    source_counts = db.get_source_counts()
    oldest, newest = db.get_date_range()

    date_range = "—"
    if oldest and newest:
        date_range = (
            f"{oldest.strftime('%Y-%m-%d')} → {newest.strftime('%Y-%m-%d')}"
        )

    sources_str = (
        ", ".join(f"{src}: {cnt}" for src, cnt in sorted(source_counts.items()))
        or "none"
    )

    console.print(
        Panel(
            f"[bold]Conversations:[/bold] {total_convs}\n"
            f"[bold]Messages:[/bold]      {total_msgs}\n"
            f"[bold]Date range:[/bold]    {date_range}\n"
            f"[bold]Sources:[/bold]       {sources_str}",
            title="[bold cyan]Vault Statistics[/bold cyan]",
            border_style="cyan",
        )
    )


@app.command("import")
def import_data(
    provider: str = typer.Argument(
        ..., help="Provider name (e.g. 'chatgpt')."
    ),
    file_path: Path = typer.Argument(
        ..., help="Path to the provider export file."
    ),
    vault_path: Path = typer.Option(
        Path("vault_data"),
        "--vault-path",
        "-p",
        help="Path to the vault directory.",
    ),
) -> None:
    """Import conversations from a provider export file.

    Supported providers: chatgpt

    Authenticates via VAULT_SESSION_TOKEN environment variable, or prompts
    for a passphrase if no valid session is found.
    """
    from vault.ingestion.pipeline import ImportPipeline
    from vault.security.crypto import KeyManager
    from vault.storage.blobs import BlobStore
    from vault.storage.db import VaultDB

    vault_path = vault_path.resolve()
    db_path = vault_path / "vault.db"
    blobs_path = vault_path / "blobs"

    # Validate vault exists
    if not db_path.exists():
        err_console.print(
            f"[red]No vault found at {vault_path}.[/red] "
            "Run [bold]vault init[/bold] first."
        )
        raise typer.Exit(code=1)

    # Validate provider
    adapters = _get_adapters()
    if provider not in adapters:
        err_console.print(
            f"[red]Unknown provider:[/red] {provider!r}. "
            f"Supported: {', '.join(sorted(adapters.keys()))}"
        )
        raise typer.Exit(code=1)

    # Validate file exists
    if not file_path.exists():
        err_console.print(f"[red]File not found:[/red] {file_path}")
        raise typer.Exit(code=1)

    # Authenticate (session token or passphrase prompt)
    master_key = _authenticate(vault_path)

    # Set up components
    km = KeyManager(vault_path)
    db = VaultDB(db_path)
    blob_store = BlobStore(blobs_path, km)
    adapter = adapters[provider]()

    # Validate file format before starting
    if not adapter.validate_format(file_path):
        err_console.print(
            f"[red]File does not appear to be a valid {provider} export:[/red] {file_path}"
        )
        raise typer.Exit(code=1)

    pipeline = ImportPipeline(db=db, blob_store=blob_store, master_key=master_key)

    console.print(
        f"[cyan]Importing[/cyan] [bold]{file_path.name}[/bold] "
        f"[cyan]via[/cyan] [bold]{provider}[/bold] adapter…"
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Importing conversations…", total=None)

        def on_progress(current: int, total: int) -> None:
            progress.update(task, completed=current, total=total)

        result = pipeline.import_conversations(
            adapter=adapter,
            file_path=file_path,
            on_progress=on_progress,
        )

    # Summary table
    table = Table(title="Import Summary", show_header=True, show_lines=False)
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")

    table.add_row("[green]Imported[/green]", str(result.imported))
    table.add_row("[yellow]Skipped (duplicates)[/yellow]", str(result.skipped))
    table.add_row("[red]Failed[/red]", str(result.failed))

    console.print()
    console.print(table)

    if result.errors:
        console.print("\n[red]Errors encountered:[/red]")
        for err in result.errors:
            console.print(f"  • {err}")

    if result.imported > 0:
        console.print(
            "\n[dim]Tip:[/dim] Run [bold cyan]vault list[/bold cyan] "
            "to browse imported conversations."
        )

    # Exit with error code if all conversations failed
    if result.failed > 0 and result.imported == 0 and result.skipped == 0:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
