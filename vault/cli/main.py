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


@app.command()
def version() -> None:
    """Print the version of the Vault CLI."""
    typer.echo("LLM Memory Vault v0.1.0")


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


if __name__ == "__main__":
    app()
