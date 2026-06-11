import json
from dataclasses import asdict
from io import StringIO
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.table import Table

from geo_seo_engine.analyzers.page_audit import audit_page as run_page_audit
from geo_seo_engine.analyzers.sitemap_audit import audit_sitemap as run_sitemap_audit
from geo_seo_engine.analyzers.site_audit import audit_site as run_site_audit
from geo_seo_engine.reporting.markdown import render_site_markdown
from geo_seo_engine.analyzers.robots_audit import audit_robots as run_robots_audit

app = typer.Typer(help="SEO + GEO operational CLI.")


@app.command()
def version() -> None:
    """Show version."""
    from geo_seo_engine import __version__

    typer.echo(__version__)


def _write_or_print(rendered: str, output: Path | None, is_json: bool = False) -> None:
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered.rstrip() + "\n", encoding="utf-8")
        typer.echo(f"Output written to {output}")
        return

    if is_json:
        typer.echo(rendered)
        return

    typer.echo(rendered, nl=False)


def _table_to_text(table: Table) -> str:
    buffer = StringIO()
    capture_console = Console(
        file=buffer,
        force_terminal=False,
        color_system=None,
        width=100,
    )
    capture_console.print(table)
    return buffer.getvalue()


def _render_page_table(result) -> str:
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

    return _table_to_text(table)


def _render_sitemap_table(result) -> str:
    table = Table(title="Sitemap Audit")
    table.add_column("Field")
    table.add_column("Value")

    table.add_row("URL", result.url)
    table.add_row("Final URL", result.final_url)
    table.add_row("Status", str(result.status_code))
    table.add_row("Content-Type", result.content_type or "—")
    table.add_row("Sitemap type", result.sitemap_type or "—")
    table.add_row("URL count", str(result.url_count))
    table.add_row("Duplicate URLs", str(len(result.duplicate_urls)))
    table.add_row("Invalid URLs", str(len(result.invalid_urls)))
    table.add_row("URLs with query", str(len(result.urls_with_query)))
    table.add_row("Off-domain URLs", str(len(result.off_domain_urls)))
    table.add_row("Missing lastmod", str(result.missing_lastmod_count))
    table.add_row("Issues", ", ".join(result.issues) if result.issues else "none")

    return _table_to_text(table)


def _render_robots_table(result) -> str:
    table = Table(title="Robots Audit")
    table.add_column("Field")
    table.add_column("Value")

    table.add_row("URL", result.url)
    table.add_row("Final URL", result.final_url)
    table.add_row("Status", str(result.status_code))
    table.add_row("Content-Type", result.content_type or "—")
    table.add_row("Line count", str(result.line_count))
    table.add_row("User-agents", ", ".join(result.user_agents) if result.user_agents else "—")
    table.add_row("Allow count", str(result.allow_count))
    table.add_row("Disallow count", str(result.disallow_count))
    table.add_row("Sitemaps", " | ".join(result.sitemap_urls) if result.sitemap_urls else "—")
    table.add_row("Crawl-delay count", str(result.crawl_delay_count))
    table.add_row("Unknown directives", str(len(result.unknown_directives)))
    table.add_row("Blocks all", "yes" if result.blocks_all else "no")
    table.add_row("Issues", ", ".join(result.issues) if result.issues else "none")

    return _table_to_text(table)


def _render_site_table(result) -> str:
    table = Table(title="Site Audit")
    table.add_column("Field")
    table.add_column("Value")

    table.add_row("URL", result.url)
    table.add_row("Score", str(result.score))
    table.add_row("Page status", str(result.page.status_code))
    table.add_row("Page title", result.page.title or "—")
    table.add_row("Page noindex", "yes" if result.page.noindex else "no")
    table.add_row("Robots status", str(result.robots.status_code))
    table.add_row("Robots blocks all", "yes" if result.robots.blocks_all else "no")
    table.add_row("Robots sitemaps", " | ".join(result.robots.sitemap_urls) if result.robots.sitemap_urls else "—")
    table.add_row("Sitemap status", str(result.sitemap.status_code))
    table.add_row("Sitemap type", result.sitemap.sitemap_type or "—")
    table.add_row("Sitemap URL count", str(result.sitemap.url_count))
    table.add_row("Structured data JSON-LD blocks", str(result.structured_data.json_ld_blocks))
    table.add_row(
        "Structured data types",
        " | ".join(result.structured_data.types) if result.structured_data.types else "—",
    )
    table.add_row("Total issues", str(len(result.issues)))
    table.add_row("Issues", ", ".join(result.issues) if result.issues else "none")

    return _table_to_text(table)


@app.command("audit-page")
def audit_page(
    url: str,
    output_format: Literal["table", "json"] = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table or json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Audit a single public HTML page."""
    result = run_page_audit(url)

    if output_format == "json":
        rendered = json.dumps(asdict(result), ensure_ascii=False, indent=2)
        _write_or_print(rendered, output, is_json=True)
        return

    _write_or_print(_render_page_table(result), output)


@app.command("audit-sitemap")
def audit_sitemap(
    url: str,
    output_format: Literal["table", "json"] = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table or json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Audit a sitemap XML or sitemap index."""
    result = run_sitemap_audit(url)

    if output_format == "json":
        rendered = json.dumps(asdict(result), ensure_ascii=False, indent=2)
        _write_or_print(rendered, output, is_json=True)
        return

    _write_or_print(_render_sitemap_table(result), output)


@app.command("audit-robots")
def audit_robots(
    url: str,
    output_format: Literal["table", "json"] = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table or json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Audit a robots.txt file."""
    result = run_robots_audit(url)

    if output_format == "json":
        rendered = json.dumps(asdict(result), ensure_ascii=False, indent=2)
        _write_or_print(rendered, output, is_json=True)
        return

    _write_or_print(_render_robots_table(result), output)


@app.command("audit-site")
def audit_site(
    url: str,
    sitemap_url: str | None = typer.Option(
        None,
        "--sitemap-url",
        help="Override sitemap URL. If omitted, robots.txt sitemap is used when available, otherwise /sitemap.xml.",
    ),
    output_format: Literal["table", "json", "markdown"] = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table or json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Run page, robots and sitemap audits for a site."""
    result = run_site_audit(url, sitemap_url=sitemap_url)

    if output_format == "json":
        rendered = json.dumps(asdict(result), ensure_ascii=False, indent=2)
        _write_or_print(rendered, output, is_json=True)
        return

    if output_format == "markdown":
        _write_or_print(render_site_markdown(result), output)
        return

    _write_or_print(_render_site_table(result), output)


if __name__ == "__main__":
    app()
