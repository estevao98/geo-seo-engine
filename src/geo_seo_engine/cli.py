import typer

app = typer.Typer(help="SEO + GEO operational CLI.")

@app.command()
def version() -> None:
    """Show version."""
    from geo_seo_engine import __version__
    typer.echo(__version__)

@app.command()
def audit_page(url: str) -> None:
    """Placeholder for page audit."""
    typer.echo(f"Audit page: {url}")

if __name__ == "__main__":
    app()
