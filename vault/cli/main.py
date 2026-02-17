"""
LLM Memory Vault CLI entry point.

Provides the `vault` command group with sub-commands for managing
the encrypted local knowledge base.
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

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
        console.print("[green]✓[/] Vault locked — session cleared.")
    else:
        console.print("[yellow]No active session found.[/]")


if __name__ == "__main__":
    app()
