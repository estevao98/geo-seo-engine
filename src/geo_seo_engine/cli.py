import json
from dataclasses import asdict
from io import StringIO
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.table import Table

from geo_seo_engine.analyzers.page_audit import audit_page as run_page_audit
from geo_seo_engine.config.loader import DEFAULT_PROJECT_CONFIG_YAML
from geo_seo_engine.config.loader import validate_project_config as run_config_validation
from geo_seo_engine.content import extract_main_content_from_html, summarize_content_extraction
from geo_seo_engine.core import normalize_url
from geo_seo_engine.crawler import CrawlOptions, crawl_site as run_crawl_site
from geo_seo_engine.images import extract_images_from_html, run_image_audit
from geo_seo_engine.i18n import extract_hreflang_from_html, run_hreflang_audit
from geo_seo_engine.inventory import build_url_inventory as run_build_url_inventory
from geo_seo_engine.performance import parse_pagespeed_result, run_performance_audit
from geo_seo_engine.rendering import (
    StaticHtmlRenderer,
    UnavailableRenderer,
    extract_render_snapshot,
    run_rendering_audit,
)
from geo_seo_engine.social import extract_social_metadata_from_html, run_social_metadata_audit
from geo_seo_engine.technical import TechnicalAuditOptions, run_technical_audit
from geo_seo_engine.analyzers.sitemap_audit import audit_sitemap as run_sitemap_audit
from geo_seo_engine.analyzers.site_audit import audit_site as run_site_audit
from geo_seo_engine.reporting.markdown import render_site_markdown
from geo_seo_engine.analyzers.robots_audit import audit_robots as run_robots_audit

app = typer.Typer(help="SEO + GEO operational CLI.")
config_app = typer.Typer(help="Project configuration commands.")
app.add_typer(config_app, name="config")


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


@app.command("init")
def init_project(
    config: Path = typer.Option(
        Path("geo-seo.yml"),
        "--config",
        "-c",
        help="Path for the project config file.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite an existing config file.",
    ),
) -> None:
    """Create a safe starter project config."""
    if config.exists() and not force:
        typer.echo(f"Config file already exists: {config}. Use --force to overwrite.", err=True)
        raise typer.Exit(code=1)

    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(DEFAULT_PROJECT_CONFIG_YAML, encoding="utf-8")
    typer.echo(f"Config file written to {config}")


@config_app.command("validate")
def validate_config(
    config: Path = typer.Option(
        Path("geo-seo.yml"),
        "--config",
        "-c",
        help="Path to the project config file.",
    ),
) -> None:
    """Validate a project config file."""
    try:
        project_config = run_config_validation(config)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Config valid: {project_config.project_name}")


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


@app.command("crawl")
def crawl(
    url: str,
    max_pages: int = typer.Option(
        25,
        "--max-pages",
        help="Maximum number of pages to fetch.",
        min=1,
    ),
    max_depth: int = typer.Option(
        2,
        "--max-depth",
        help="Maximum link depth to enqueue. The start URL is depth 0.",
        min=0,
    ),
    output_format: Literal["json"] = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json.",
    ),
    allowed_hosts: list[str] | None = typer.Option(
        None,
        "--allowed-host",
        help="Allowed host. Defaults to the start URL host. Can be repeated.",
    ),
    include_patterns: list[str] | None = typer.Option(
        None,
        "--include-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    exclude_patterns: list[str] | None = typer.Option(
        None,
        "--exclude-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Crawl internal links with a bounded FIFO frontier."""
    options = CrawlOptions(
        allowed_hosts=allowed_hosts or [],
        max_pages=max_pages,
        max_depth=max_depth,
        include_patterns=include_patterns or [],
        exclude_patterns=exclude_patterns or [],
    )
    result = run_crawl_site(url, options=options)

    if output_format == "json":
        rendered = json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
        _write_or_print(rendered, output, is_json=True)
        return


@app.command("extract-content")
def extract_content(
    url: str,
    max_pages: int = typer.Option(
        25,
        "--max-pages",
        help="Maximum number of pages to fetch before extracting main content.",
        min=1,
    ),
    max_depth: int = typer.Option(
        2,
        "--max-depth",
        help="Maximum link depth to enqueue. The start URL is depth 0.",
        min=0,
    ),
    allowed_hosts: list[str] | None = typer.Option(
        None,
        "--allowed-host",
        help="Allowed host. Defaults to the start URL host. Can be repeated.",
    ),
    include_patterns: list[str] | None = typer.Option(
        None,
        "--include-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    exclude_patterns: list[str] | None = typer.Option(
        None,
        "--exclude-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    output_format: Literal["json"] = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Crawl HTML pages and extract structured main content from crawl-time HTML."""
    crawl_options = CrawlOptions(
        allowed_hosts=allowed_hosts or [],
        max_pages=max_pages,
        max_depth=max_depth,
        include_patterns=include_patterns or [],
        exclude_patterns=exclude_patterns or [],
    )
    effective_allowed_hosts = allowed_hosts or [_normalized_host(url)]
    pages = []

    def collect_main_content(
        page_url: str,
        normalized_url: str,
        final_url: str,
        html: str,
        content_type: str | None,
        depth: int,
    ) -> None:
        del page_url, content_type, depth
        content_page_url = final_url or normalized_url
        pages.append(
            extract_main_content_from_html(
                html,
                content_page_url,
                allowed_hosts=effective_allowed_hosts,
            )
        )

    crawl_result = run_crawl_site(
        url,
        options=crawl_options,
        on_html_page=collect_main_content,
    )
    result = summarize_content_extraction(pages, start_url=crawl_result.start_url)

    if output_format == "json":
        rendered = json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        _write_or_print(rendered, output, is_json=True)
        return


@app.command("inventory")
def inventory(
    url: str,
    max_pages: int = typer.Option(
        25,
        "--max-pages",
        help="Maximum number of pages to fetch before building the inventory.",
        min=1,
    ),
    max_depth: int = typer.Option(
        2,
        "--max-depth",
        help="Maximum link depth to enqueue. The start URL is depth 0.",
        min=0,
    ),
    output_format: Literal["json"] = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json.",
    ),
    allowed_hosts: list[str] | None = typer.Option(
        None,
        "--allowed-host",
        help="Allowed host. Defaults to the start URL host. Can be repeated.",
    ),
    include_patterns: list[str] | None = typer.Option(
        None,
        "--include-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    exclude_patterns: list[str] | None = typer.Option(
        None,
        "--exclude-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Crawl a site and summarize fetched URLs for later audits."""
    crawl_result = run_crawl_site(
        url,
        options=CrawlOptions(
            allowed_hosts=allowed_hosts or [],
            max_pages=max_pages,
            max_depth=max_depth,
            include_patterns=include_patterns or [],
            exclude_patterns=exclude_patterns or [],
        ),
    )
    result = run_build_url_inventory(crawl_result)

    if output_format == "json":
        rendered = json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2)
        _write_or_print(rendered, output, is_json=True)
        return


@app.command("audit-images")
def audit_images(
    url: str,
    max_pages: int = typer.Option(
        25,
        "--max-pages",
        help="Maximum number of pages to fetch before auditing image tags.",
        min=1,
    ),
    max_depth: int = typer.Option(
        2,
        "--max-depth",
        help="Maximum link depth to enqueue. The start URL is depth 0.",
        min=0,
    ),
    allowed_hosts: list[str] | None = typer.Option(
        None,
        "--allowed-host",
        help="Allowed host. Defaults to the start URL host. Can be repeated.",
    ),
    include_patterns: list[str] | None = typer.Option(
        None,
        "--include-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    exclude_patterns: list[str] | None = typer.Option(
        None,
        "--exclude-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    output_format: Literal["json"] = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Crawl HTML pages and audit static image tags without downloading image files."""
    crawl_options = CrawlOptions(
        allowed_hosts=allowed_hosts or [],
        max_pages=max_pages,
        max_depth=max_depth,
        include_patterns=include_patterns or [],
        exclude_patterns=exclude_patterns or [],
    )
    effective_allowed_hosts = allowed_hosts or [_normalized_host(url)]
    page_inventories = []

    def collect_images_from_html(
        page_url: str,
        normalized_url: str,
        final_url: str,
        html: str,
        content_type: str | None,
        depth: int,
    ) -> None:
        del normalized_url, content_type, depth
        inventory_page_url = final_url or page_url
        page_inventories.append(
            extract_images_from_html(
                html,
                inventory_page_url,
                allowed_hosts=effective_allowed_hosts,
            )
        )

    crawl_result = run_crawl_site(
        url,
        options=crawl_options,
        on_html_page=collect_images_from_html,
    )

    result = run_image_audit(
        page_inventories,
        start_url=crawl_result.start_url,
    )

    if output_format == "json":
        rendered = json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        _write_or_print(rendered, output, is_json=True)
        return


@app.command("audit-social")
def audit_social(
    url: str,
    max_pages: int = typer.Option(
        25,
        "--max-pages",
        help="Maximum number of pages to fetch before auditing social metadata.",
        min=1,
    ),
    max_depth: int = typer.Option(
        2,
        "--max-depth",
        help="Maximum link depth to enqueue. The start URL is depth 0.",
        min=0,
    ),
    allowed_hosts: list[str] | None = typer.Option(
        None,
        "--allowed-host",
        help="Allowed host. Defaults to the start URL host. Can be repeated.",
    ),
    include_patterns: list[str] | None = typer.Option(
        None,
        "--include-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    exclude_patterns: list[str] | None = typer.Option(
        None,
        "--exclude-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    output_format: Literal["json"] = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Crawl HTML pages and audit static Open Graph and Twitter/X metadata."""
    crawl_options = CrawlOptions(
        allowed_hosts=allowed_hosts or [],
        max_pages=max_pages,
        max_depth=max_depth,
        include_patterns=include_patterns or [],
        exclude_patterns=exclude_patterns or [],
    )
    effective_allowed_hosts = allowed_hosts or [_normalized_host(url)]
    page_metadata = []

    def collect_social_metadata_from_html(
        page_url: str,
        normalized_url: str,
        final_url: str,
        html: str,
        content_type: str | None,
        depth: int,
    ) -> None:
        del normalized_url, content_type, depth
        metadata_page_url = final_url or page_url
        page_metadata.append(
            extract_social_metadata_from_html(
                html,
                metadata_page_url,
                allowed_hosts=effective_allowed_hosts,
            )
        )

    crawl_result = run_crawl_site(
        url,
        options=crawl_options,
        on_html_page=collect_social_metadata_from_html,
    )

    result = run_social_metadata_audit(
        page_metadata,
        start_url=crawl_result.start_url,
    )

    if output_format == "json":
        rendered = json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        _write_or_print(rendered, output, is_json=True)
        return


@app.command("audit-hreflang")
def audit_hreflang(
    url: str,
    max_pages: int = typer.Option(
        25,
        "--max-pages",
        help="Maximum number of pages to fetch before auditing hreflang tags.",
        min=1,
    ),
    max_depth: int = typer.Option(
        2,
        "--max-depth",
        help="Maximum link depth to enqueue. The start URL is depth 0.",
        min=0,
    ),
    allowed_hosts: list[str] | None = typer.Option(
        None,
        "--allowed-host",
        help="Allowed host. Defaults to the start URL host. Can be repeated.",
    ),
    include_patterns: list[str] | None = typer.Option(
        None,
        "--include-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    exclude_patterns: list[str] | None = typer.Option(
        None,
        "--exclude-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    output_format: Literal["json"] = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Crawl HTML pages and audit static hreflang alternate annotations."""
    crawl_options = CrawlOptions(
        allowed_hosts=allowed_hosts or [],
        max_pages=max_pages,
        max_depth=max_depth,
        include_patterns=include_patterns or [],
        exclude_patterns=exclude_patterns or [],
    )
    effective_allowed_hosts = allowed_hosts or [_normalized_host(url)]
    page_inventories = []

    def collect_hreflang_from_html(
        page_url: str,
        normalized_url: str,
        final_url: str,
        html: str,
        content_type: str | None,
        depth: int,
    ) -> None:
        del page_url, content_type, depth
        inventory_page_url = final_url or normalized_url
        page_inventories.append(
            extract_hreflang_from_html(
                html,
                inventory_page_url,
                allowed_hosts=effective_allowed_hosts,
            )
        )

    crawl_result = run_crawl_site(
        url,
        options=crawl_options,
        on_html_page=collect_hreflang_from_html,
    )

    result = run_hreflang_audit(
        page_inventories,
        start_url=crawl_result.start_url,
    )

    if output_format == "json":
        rendered = json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        _write_or_print(rendered, output, is_json=True)
        return


@app.command("audit-technical")
def audit_technical(
    url: str,
    max_pages: int = typer.Option(
        25,
        "--max-pages",
        help="Maximum number of pages to fetch before auditing the inventory.",
        min=1,
    ),
    max_depth: int = typer.Option(
        2,
        "--max-depth",
        help="Maximum link depth to enqueue. The start URL is depth 0.",
        min=0,
    ),
    max_depth_warning: int = typer.Option(
        3,
        "--max-depth-warning",
        help="Depth above which a fetched URL receives a technical warning.",
        min=0,
    ),
    high_skipped_urls_warning: int = typer.Option(
        25,
        "--high-skipped-urls-warning",
        help="Skipped URL count above which the audit emits a warning.",
        min=0,
    ),
    flag_non_html: bool = typer.Option(
        True,
        "--non-html-findings/--no-non-html-findings",
        help="Emit inventory findings for discovered non-HTML URLs.",
    ),
    flag_redirects: bool = typer.Option(
        True,
        "--redirect-findings/--no-redirect-findings",
        help="Emit findings for discovered URLs that redirect.",
    ),
    flag_zero_links: bool = typer.Option(
        True,
        "--zero-links-findings/--no-zero-links-findings",
        help="Emit findings when the crawler extracts zero static links.",
    ),
    allowed_hosts: list[str] | None = typer.Option(
        None,
        "--allowed-host",
        help="Allowed host. Defaults to the start URL host. Can be repeated.",
    ),
    include_patterns: list[str] | None = typer.Option(
        None,
        "--include-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    exclude_patterns: list[str] | None = typer.Option(
        None,
        "--exclude-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    output_format: Literal["json"] = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Crawl a site inventory and emit technical SEO/GEO findings."""
    crawl_result = run_crawl_site(
        url,
        options=CrawlOptions(
            allowed_hosts=allowed_hosts or [],
            max_pages=max_pages,
            max_depth=max_depth,
            include_patterns=include_patterns or [],
            exclude_patterns=exclude_patterns or [],
        ),
    )
    inventory_result = run_build_url_inventory(crawl_result)
    result = run_technical_audit(
        inventory_result,
        options=TechnicalAuditOptions(
            max_depth_warning=max_depth_warning,
            high_skipped_urls_warning=high_skipped_urls_warning,
            flag_non_html=flag_non_html,
            flag_redirects=flag_redirects,
            flag_zero_links=flag_zero_links,
        ),
    )

    if output_format == "json":
        rendered = json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        _write_or_print(rendered, output, is_json=True)
        return


@app.command("audit-rendering")
def audit_rendering(
    url: str,
    max_pages: int = typer.Option(
        10,
        "--max-pages",
        help="Maximum number of pages to fetch before auditing rendering differences.",
        min=1,
    ),
    max_depth: int = typer.Option(
        1,
        "--max-depth",
        help="Maximum link depth to enqueue. The start URL is depth 0.",
        min=0,
    ),
    allowed_hosts: list[str] | None = typer.Option(
        None,
        "--allowed-host",
        help="Allowed host. Defaults to the start URL host. Can be repeated.",
    ),
    include_patterns: list[str] | None = typer.Option(
        None,
        "--include-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    exclude_patterns: list[str] | None = typer.Option(
        None,
        "--exclude-pattern",
        help="fnmatch pattern for normalized URL or path. Can be repeated.",
    ),
    renderer_name: Literal["none", "static"] = typer.Option(
        "none",
        "--renderer",
        help="Renderer to use. 'static' is a no-browser test mode; 'none' fails gracefully.",
    ),
    output_format: Literal["json"] = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
) -> None:
    """Optionally compare crawl-time HTML with rendered HTML signals."""
    if renderer_name == "none":
        typer.echo(
            "No JavaScript renderer is configured. Pass --renderer static for static test mode or integrate a PageRenderer implementation.",
            err=True,
        )
        raise typer.Exit(code=1)

    renderer = StaticHtmlRenderer() if renderer_name == "static" else UnavailableRenderer()
    crawl_options = CrawlOptions(
        allowed_hosts=allowed_hosts or [],
        max_pages=max_pages,
        max_depth=max_depth,
        include_patterns=include_patterns or [],
        exclude_patterns=exclude_patterns or [],
    )
    pages = []

    def collect_render_snapshot(
        page_url: str,
        normalized_url: str,
        final_url: str,
        html: str,
        content_type: str | None,
        depth: int,
    ) -> None:
        del page_url, content_type, depth
        snapshot_url = final_url or normalized_url
        rendered_page = renderer.render(snapshot_url, html=html)
        pages.append(
            extract_render_snapshot(
                snapshot_url,
                html,
                rendered_html=rendered_page.html,
                render_error=rendered_page.error,
                render_status=rendered_page.status,
            )
        )

    crawl_result = run_crawl_site(
        url,
        options=crawl_options,
        on_html_page=collect_render_snapshot,
    )
    result = run_rendering_audit(pages, start_url=crawl_result.start_url)

    if output_format == "json":
        rendered = json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        _write_or_print(rendered, output, is_json=True)
        return


@app.command("audit-performance")
def audit_performance(
    input_path: Path = typer.Option(
        ...,
        "--input",
        help="Local PageSpeed/Lighthouse-style JSON payload to import.",
    ),
    output_format: Literal["json"] = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write output to a file.",
    ),
    page_url: str | None = typer.Option(
        None,
        "--page-url",
        help="Override the page URL stored in the imported payload.",
    ),
) -> None:
    """Audit a local PageSpeed/Lighthouse-style JSON payload without external calls."""
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except OSError as exc:
        typer.echo(f"Could not read input JSON: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except json.JSONDecodeError as exc:
        typer.echo(f"Invalid input JSON: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if not isinstance(payload, dict):
        typer.echo("Input JSON must be an object.", err=True)
        raise typer.Exit(code=1)

    snapshot = parse_pagespeed_result(payload, page_url=page_url)
    result = run_performance_audit([snapshot], start_url=snapshot.page_url)

    if output_format == "json":
        rendered = json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        _write_or_print(rendered, output, is_json=True)
        return


def _normalized_host(url: str) -> str:
    return normalize_url(url).host


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
