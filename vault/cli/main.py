"""Command-line interface for the LLM Memory Vault."""
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer()
console = Console()


@app.command()
def version() -> None:
    """Print the version of the Vault CLI."""
    typer.echo("LLM Memory Vault v0.1.0")


@app.command("list")
def list_conversations(
    limit: int = typer.Option(20, help="Number of conversations to show"),
    offset: int = typer.Option(0, help="Skip N conversations"),
    source: str = typer.Option(None, help="Filter by source (e.g., 'chatgpt')"),
    vault_path: Path = typer.Option(Path("vault_data"), help="Path to vault"),
) -> None:
    """List conversations stored in the vault."""
    db_file = vault_path / "vault.db"
    if not db_file.exists():
        console.print(
            "[red]Vault not initialized.[/red] Run [bold]vault init[/bold] first."
        )
        raise typer.Exit(code=1)

    from vault.storage.db import VaultDB

    db = VaultDB(db_path=db_file)
    conversations = db.list_conversations(limit=limit, offset=offset, source=source)
    total = db.count_conversations()

    if not conversations:
        console.print("No conversations found. Import some with: vault import chatgpt <file>")
        return

    table = Table(title="Vault Conversations")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white", max_width=40)
    table.add_column("Source", style="green")
    table.add_column("Date", style="yellow")
    table.add_column("Msgs", style="magenta", justify="right")

    for conv in conversations:
        table.add_row(
            conv.id[:8],
            (conv.title[:40] + "...") if len(conv.title) > 40 else conv.title,
            conv.source,
            conv.created_at.strftime("%Y-%m-%d") if conv.created_at else "—",
            str(conv.message_count),
        )

    console.print(table)
    console.print(f"Showing {len(conversations)} of {total:,} conversations")


@app.command()
def stats(
    vault_path: Path = typer.Option(Path("vault_data"), help="Path to vault"),
) -> None:
    """Display vault statistics."""
    db_file = vault_path / "vault.db"
    if not db_file.exists():
        console.print(
            "[red]Vault not initialized.[/red] Run [bold]vault init[/bold] first."
        )
        raise typer.Exit(code=1)

    from vault.security.crypto import KeyManager
    from vault.storage.blobs import BlobStore
    from vault.storage.db import VaultDB

    db = VaultDB(db_path=db_file)
    blob_root = vault_path / "blobs"
    key_manager = KeyManager(vault_root=vault_path)
    blob_store = BlobStore(root_path=blob_root, key_manager=key_manager)

    total_convos = db.count_conversations()
    total_msgs = db.count_messages()
    source_counts = db.get_source_counts()
    oldest, newest = db.get_date_range()
    storage_bytes = blob_store.get_total_size()

    # Format storage size
    if storage_bytes >= 1_073_741_824:
        storage_str = f"{storage_bytes / 1_073_741_824:.1f} GB"
    elif storage_bytes >= 1_048_576:
        storage_str = f"{storage_bytes / 1_048_576:.1f} MB"
    elif storage_bytes >= 1024:
        storage_str = f"{storage_bytes / 1024:.1f} KB"
    else:
        storage_str = f"{storage_bytes} B"

    # Build stats content
    lines = [
        f"  Total Conversations:  {total_convos:,}",
        f"  Total Messages:       {total_msgs:,}",
        f"  Encrypted Storage:    {storage_str}",
    ]

    if source_counts:
        lines.append("")
        lines.append("  Sources:")
        for src, count in sorted(source_counts.items()):
            lines.append(f"    {src}:  {count:,}")

    if oldest and newest:
        lines.append("")
        lines.append("  Date Range:")
        lines.append(f"    Oldest:  {oldest.strftime('%Y-%m-%d')}")
        lines.append(f"    Newest:  {newest.strftime('%Y-%m-%d')}")
    elif total_convos == 0:
        lines.append("")
        lines.append("  No conversations yet")

    panel = Panel(
        "\n".join(lines),
        title="Vault Statistics",
        expand=False,
    )
    console.print(panel)


if __name__ == "__main__":
    app()
