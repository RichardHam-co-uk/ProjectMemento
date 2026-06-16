from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
import yaml

from vault.memory.models import MemoryStatus, StagedMemoryRequest
from vault.memory.store import (
    DuplicateMemoryError,
    FileMemoryStore,
    MemoryFilters,
    MemoryNotFoundError,
)

app = typer.Typer(help="ProjectMemento local vault CLI")
memory_app = typer.Typer(help="Minimal deterministic memory commands")
app.add_typer(memory_app, name="memory")


def _store(root: Optional[Path]) -> FileMemoryStore:
    return FileMemoryStore(root or Path("vault_data"))


@app.command()
def version():
    """Print the version of the Vault CLI."""
    typer.echo("ProjectMemento Vault v0.1.0")


@app.command()
def init(
    root: Optional[Path] = typer.Option(
        None, "--root", help="Vault root directory (default: vault_data)"
    )
):
    """Initialise the local Phase 1 memory store."""
    path = _store(root).init()
    typer.echo(f"Initialised memory store: {path}")


@memory_app.command("stage")
def memory_stage(
    file: Path = typer.Argument(..., exists=True, readable=True),
    root: Optional[Path] = typer.Option(None, "--root", help="Vault root directory"),
):
    """Stage a memory from a YAML or JSON file."""
    payload = _load_payload(file)
    request = StagedMemoryRequest.model_validate(payload)
    try:
        record = _store(root).stage(request)
    except DuplicateMemoryError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(record.id)


@memory_app.command("list")
def memory_list(
    root: Optional[Path] = typer.Option(None, "--root", help="Vault root directory"),
    status: Optional[MemoryStatus] = typer.Option(None, "--status"),
    namespace: Optional[str] = typer.Option(None, "--namespace"),
    memory_type: Optional[str] = typer.Option(None, "--type"),
    sensitivity: Optional[str] = typer.Option(None, "--sensitivity"),
    query: Optional[str] = typer.Option(None, "--query"),
):
    """List memory records with optional governance filters."""
    records = _store(root).list(
        MemoryFilters(
            status=status,
            namespace=namespace,
            memory_type=memory_type,
            sensitivity=sensitivity,
            query=query,
        )
    )
    for record in records:
        typer.echo(
            f"{record.id}\t{record.status.value}\t{record.type.value}\t"
            f"{record.namespace}\t{record.sensitivity.value}\t{record.title}"
        )


@memory_app.command("show")
def memory_show(
    memory_id: str,
    root: Optional[Path] = typer.Option(None, "--root", help="Vault root directory"),
    include_body: bool = typer.Option(False, "--include-body"),
):
    """Show a single memory record as JSON."""
    try:
        record = _store(root).get(memory_id)
    except MemoryNotFoundError as exc:
        raise typer.BadParameter(f"memory not found: {memory_id}") from exc
    typer.echo(json.dumps(record.safe_view(include_body=include_body), indent=2, sort_keys=True))


@memory_app.command("approve")
def memory_approve(
    memory_id: str,
    root: Optional[Path] = typer.Option(None, "--root", help="Vault root directory"),
    approved_by: str = typer.Option("local", "--approved-by"),
):
    """Approve a staged memory so it is eligible for retrieval."""
    try:
        record = _store(root).approve(memory_id, approved_by=approved_by)
    except MemoryNotFoundError as exc:
        raise typer.BadParameter(f"memory not found: {memory_id}") from exc
    typer.echo(f"{record.id}\t{record.status.value}")


@memory_app.command("reject")
def memory_reject(
    memory_id: str,
    reason: str = typer.Option(..., "--reason"),
    root: Optional[Path] = typer.Option(None, "--root", help="Vault root directory"),
):
    """Reject a staged memory while keeping an audit trail."""
    try:
        record = _store(root).reject(memory_id, reason=reason)
    except MemoryNotFoundError as exc:
        raise typer.BadParameter(f"memory not found: {memory_id}") from exc
    typer.echo(f"{record.id}\t{record.status.value}\t{record.status_reason}")


@memory_app.command("search")
def memory_search(
    query: str,
    root: Optional[Path] = typer.Option(None, "--root", help="Vault root directory"),
    namespace: Optional[str] = typer.Option(None, "--namespace"),
    include_staged: bool = typer.Option(False, "--include-staged"),
):
    """Search approved memory records by keyword."""
    records = _store(root).search(query, namespace=namespace, include_staged=include_staged)
    for record in records:
        typer.echo(f"{record.id}\t{record.namespace}\t{record.title}")


def _load_payload(file: Path) -> dict:
    text = file.read_text(encoding="utf-8")
    if file.suffix.lower() == ".json":
        return json.loads(text)
    loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise typer.BadParameter("memory input must be a YAML/JSON object")
    return loaded


if __name__ == "__main__":
    app()
