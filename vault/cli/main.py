"""Vault CLI entry point."""
import typer
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from typing import Optional, List

from vault.config.models import VaultConfig
from vault.storage.db import VaultDB
from vault.storage.blobs import BlobStore
from vault.security.crypto import KeyManager
from vault.security.session import SessionManager

app = typer.Typer(help="LLM Memory Vault CLI")
console = Console()
config = VaultConfig()


def get_authenticated_key(passphrase: Optional[str] = None) -> bytes:
    """Get the master key, using session if active or prompting for passphrase."""
    vault_root = config.vault_root
    session_manager = SessionManager(vault_root, timeout_minutes=config.security.session_timeout_minutes)
    key_manager = KeyManager(vault_root)

    # 1. Try session first
    # For CLI, we might store token in an environment variable or a local file.
    # The requirement says "Raw token never stored on disk".
    # However, usually there's a small local cache or we expect VAULT_TOKEN env var.
    # Let's check for VAULT_TOKEN.
    import os
    token = os.environ.get("VAULT_TOKEN")
    if token:
        key = session_manager.validate_token(token)
        if key:
            return key

    # 2. Use provided passphrase
    if passphrase:
        try:
            return key_manager.derive_master_key(passphrase)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)

    # 3. Prompt for passphrase
    passphrase = Prompt.ask("Enter master passphrase", password=True)
    try:
        key = key_manager.derive_master_key(passphrase)
        
        # Propose creating a session
        if not token:
            if Prompt.ask("Create session for 30 minutes?", choices=["y", "n"], default="y") == "y":
                new_token = session_manager.create_session(key)
                console.print(f"Session created. To avoid re-entering passphrase, run:")
                console.print(f"  [bold]set VAULT_TOKEN={new_token}[/bold] (Windows)")
                console.print(f"  [bold]export VAULT_TOKEN={new_token}[/bold] (Unix)")
        
        return key
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing vault")
):
    """Initialize a new empty vault.
    
    Sets up the directory structure, initializes the database schema,
    and configures the master key.
    """
    vault_root = config.vault_root
    salt_file = vault_root / ".salt"
    
    if salt_file.exists() and not force:
        console.print(f"[red]Vault already initialized at {vault_root}. Use --force to overwrite.[/red]")
        raise typer.Exit(code=1)
    
    if force and vault_root.exists():
        console.print(f"[yellow]Warning: Overwriting vault configuration at {vault_root}![/yellow]")
    
    console.print(f"Initializing vault at [bold]{vault_root}[/bold]...")
    
    # 1. Ensure root exists
    try:
        vault_root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(f"[red]Error creating vault directory:[/red] {e}")
        raise typer.Exit(code=1)
    
    # 2. Setup Security (KeyManager)
    # This just prepares the class; derivation handles the salt file
    key_manager = KeyManager(vault_root)
    
    passphrase = Prompt.ask("Enter a master passphrase", password=True)
    confirm = Prompt.ask("Confirm passphrase", password=True)
    
    if passphrase != confirm:
        console.print("[red]Passphrases do not match![/red]")
        raise typer.Exit(code=1)
    
    try:
        # This creates the .salt file and validates passphrase length
        key_manager.derive_master_key(passphrase)
        console.print("[green]✔[/green] Encryption keys initialized.")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(code=1)
        
    # 3. Setup Database
    db_path = config.database.db_path
    try:
        db = VaultDB(db_path, echo=config.database.echo_sql)
        db.init_schema()
        console.print(f"[green]✔[/green] Database initialized at {db_path}.")
    except Exception as e:
        console.print(f"[red]Database initialization failed:[/red] {e}")
        raise typer.Exit(code=1)
    
    # 4. Setup BlobStore
    blob_path = config.blobs.storage_path
    try:
        # Just init to create directories
        BlobStore(blob_path, key_manager)
        console.print(f"[green]✔[/green] Blob storage initialized at {blob_path}.")
    except Exception as e:
        console.print(f"[red]Blob store initialization failed:[/red] {e}")
        raise typer.Exit(code=1)
    
    console.print("\n[bold green]Vault initialization complete![/bold green]")


@app.command("import")
def import_cmd(
    file_path: Path = typer.Argument(..., help="Path to export file", exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    provider: str = typer.Option("chatgpt", "--provider", "-p", help="Provider name (chatgpt)"),
    passphrase: Optional[str] = typer.Option(None, "--passphrase", help="Vault passphrase", hide_input=True)
):
    """Import conversations from an export file."""
    vault_root = config.vault_root
    
    if not vault_root.exists():
        console.print(f"[red]Vault not initialized at {vault_root}. Run 'vault init' first.[/red]")
        raise typer.Exit(code=1)

    master_key = get_authenticated_key(passphrase)
    key_manager = KeyManager(vault_root)
        
    # Init components
    db_path = config.database.db_path
    db = VaultDB(db_path, echo=False)
    blob_store = BlobStore(config.blobs.storage_path, key_manager)
    
    # Run pipeline
    from vault.ingestion.pipeline import ImportPipeline
    
    pipeline = ImportPipeline(db, blob_store, key_manager, master_key)
    
    console.print(f"Starting import from [bold]{file_path.name}[/bold]...")
    with console.status("Processing...") as status:
        result = pipeline.run(file_path, provider=provider)
        
    # Report results
    console.print("\n[bold]Import Summary:[/bold]")
    console.print(f"  Imported: [green]{result.imported}[/green]")
    console.print(f"  Skipped:  [yellow]{result.skipped}[/yellow] (duplicates)")
    console.print(f"  Failed:   [red]{result.failed}[/red]")
    
    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for err in result.errors[:10]: # Limit error output
            console.print(f"  - {err}")
        if len(result.errors) > 10:
            console.print(f"  ...and {len(result.errors) - 10} more.")


@app.command("list")
def list_cmd(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of items to show"),
    offset: int = typer.Option(0, "--offset", help="Number of items to skip"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by provider"),
):
    """List conversations in the vault."""
    db = VaultDB(config.database.db_path)
    convs = db.list_conversations(limit=limit, offset=offset, source=source)
    
    if not convs:
        console.print("No conversations found.")
        return

    table = Table(title="Vault Conversations")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Source", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Messages", justify="right")
    table.add_column("Created At", style="blue")

    for c in convs:
        table.add_row(
            c.id[:8], 
            c.source, 
            c.title, 
            str(c.message_count), 
            c.created_at.strftime("%Y-%m-%d %H:%M")
        )

    console.print(table)


@app.command("show")
def show_cmd(
    conv_id: str = typer.Argument(..., help="Conversation hash or prefix"),
    passphrase: Optional[str] = typer.Option(None, "--passphrase", help="Vault passphrase", hide_input=True)
):
    """Show details and messages of a conversation."""
    db = VaultDB(config.database.db_path)
    
    # Prefix search support
    if len(conv_id) < 64:
        # Search for full ID
        convs = db.list_conversations(limit=10) # Simple prefix search not in db yet, we'll just match exact or warn
        match = None
        for c in convs:
            if c.id.startswith(conv_id):
                match = c
                break
        if not match:
            console.print(f"[red]Conversation starting with {conv_id} not found.[/red]")
            return
        conv = match
    else:
        conv = db.get_conversation(conv_id)

    if not conv:
        console.print(f"[red]Conversation {conv_id} not found.[/red]")
        return

    console.print(Panel(f"[bold]{conv.title}[/bold]\nSource: {conv.source} | Created: {conv.created_at}", title="Conversation Info"))
    
    messages = db.get_messages_for_conversation(conv.id)
    if not messages:
        console.print("No messages found.")
        return

    # Authenticate for decryption
    master_key = get_authenticated_key(passphrase)
    key_manager = KeyManager(config.vault_root)
    blob_store = BlobStore(config.blobs.storage_path, key_manager)

    for m in messages:
        try:
            content = blob_store.retrieve(m.content_blob_uuid, master_key, conv.id)
            text = content.decode("utf-8")
        except Exception as e:
            text = f"[red]Error decrypting message: {e}[/red]"
        
        author_style = "bold blue" if m.actor == "user" else "bold green"
        console.print(f"\n[{author_style}]{m.actor.upper()}[/{author_style}] ({m.timestamp.strftime('%H:%M:%S')})")
        console.print(text)


@app.command("stats")
def stats_cmd():
    """Show vault statistics."""
    db = VaultDB(config.database.db_path)
    
    conv_count = db.count_conversations()
    msg_count = db.count_messages()
    date_range = db.get_date_range()
    source_counts = db.get_source_counts()
    
    blob_store = BlobStore(config.blobs.storage_path, KeyManager(config.vault_root))
    total_bytes = blob_store.get_total_size()
    
    stats_text = f"""
Conversations: [bold]{conv_count}[/bold]
Total Messages: [bold]{msg_count}[/bold]
Storage Size: [bold]{total_bytes / 1024:.2f} KB[/bold]
"""
    if date_range[0] and date_range[1]:
        stats_text += f"Date Range: [bold]{date_range[0].date()}[/bold] to [bold]{date_range[1].date()}[/bold]\n"

    if source_counts:
        stats_text += "\n[bold]By Source:[/bold]\n"
        for src, count in source_counts.items():
            stats_text += f"  - {src}: {count}\n"

    console.print(Panel(stats_text.strip(), title="Vault Statistics"))


@app.command("lock")
def lock_cmd():
    """Clear the active session."""
    session_manager = SessionManager(config.vault_root)
    if session_manager.is_active():
        session_manager.clear_session()
        console.print("[green]Session cleared. Vault locked.[/green]")
    else:
        console.print("No active session found.")


@app.command()
def version():
    """Print the version of the Vault CLI."""
    console.print("LLM Memory Vault v0.1.0")


if __name__ == "__main__":
    app()
