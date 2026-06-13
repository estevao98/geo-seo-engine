import json

import pytest
from typer.testing import CliRunner

from geo_seo_engine.cli import app
from geo_seo_engine.crawler import CrawlPage, CrawlResult


runner = CliRunner()


@pytest.mark.parametrize(
    ("command", "expected_terms"),
    [
        ("crawl", ["Crawl internal links", "--max-pages", "--max-depth"]),
        ("inventory", ["summarize fetched URLs", "--max-pages", "--max-depth"]),
        (
            "audit-technical",
            ["technical SEO/GEO findings", "Depth above", "zero", "static links"],
        ),
    ],
)
def test_cli_foundation_command_help(command, expected_terms):
    result = runner.invoke(app, [command, "--help"])

    assert result.exit_code == 0
    for term in expected_terms:
        assert term in result.output


def test_cli_foundation_crawl_uses_injected_crawler(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None):
        assert url == "https://example.com"
        assert options.max_pages == 2
        assert options.max_depth == 1
        return _crawl_result(links_found=1)

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        ["crawl", "https://example.com", "--max-pages", "2", "--max-depth", "1"],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["pages"][0]["status_code"] == 200


def test_cli_foundation_inventory_uses_injected_crawler(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None):
        assert url == "https://example.com"
        return _crawl_result(links_found=1)

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(app, ["inventory", "https://example.com"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["summary"]["total_pages"] == 1
    assert data["summary"]["html_pages"] == 1


def test_cli_foundation_audit_technical_uses_injected_crawler(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None):
        assert url == "https://example.com"
        return _crawl_result(links_found=0)

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(app, ["audit-technical", "https://example.com"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["findings"][0]["id"] == "technical.zero_links_found"
    assert data["summary"]["total_findings"] == 1


def _crawl_result(*, links_found: int) -> CrawlResult:
    return CrawlResult(
        start_url="https://example.com/",
        pages=[
            CrawlPage(
                url="https://example.com/",
                normalized_url="https://example.com/",
                final_url="https://example.com/",
                status_code=200,
                depth=0,
                content_type="text/html",
                links_found=links_found,
            )
        ],
    )
