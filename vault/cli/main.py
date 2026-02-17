import typer

app = typer.Typer()

@app.command()
def version():
    """Print the version of the Vault CLI."""
    typer.echo("LLM Memory Vault v0.1.0")

if __name__ == "__main__":
    app()
