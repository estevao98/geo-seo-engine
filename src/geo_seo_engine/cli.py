import json
from dataclasses import asdict
from typing import Literal

import typer
from rich.console import Console
from rich.table import Table

from geo_seo_engine.analyzers.page_audit import audit_page as run_page_audit

app = typer.Typer(help="SEO + GEO operational CLI.")
console = Console()


@app.command()
def version() -> None:
    """Show version."""
    from geo_seo_engine import __version__

    typer.echo(__version__)


@app.command("audit-page")
def audit_page(
    url: str,
    output_format: Literal["table", "json"] = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table or json.",
    ),
) -> None:
    """Audit a single public HTML page."""
    result = run_page_audit(url)

    if output_format == "json":
        typer.echo(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return

    table = Table(title="Page Audit")
    table.add_column("Field")
    table.add_column("Value")

    table.add_row("URL", result.url)
    table.add_row("Final URL", result.final_url)
    table.add_row("Status", str(result.status_code))
    table.add_row("Title", result.title or "—")
    table.add_row("Meta description", result.meta_description or "—")
    table.add_row("H1", " | ".join(result.h1) if result.h1 else "—")
    table.add_row("Canonical", result.canonical or "—")
    table.add_row("Meta robots", result.meta_robots or "—")
    table.add_row("Noindex", "yes" if result.noindex else "no")
    table.add_row("Internal links", str(result.internal_links))
    table.add_row("External links", str(result.external_links))
    table.add_row("Issues", ", ".join(result.issues) if result.issues else "none")

    console.print(table)


if __name__ == "__main__":
    app()
