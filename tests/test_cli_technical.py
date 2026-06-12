import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app
from geo_seo_engine.crawler import CrawlPage, CrawlResult
from geo_seo_engine.technical import TechnicalAuditResult, TechnicalAuditSummary

runner = CliRunner()


def test_cli_audit_technical_returns_valid_json(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None):
        assert url == "https://example.com"
        assert options.max_pages == 25
        assert options.max_depth == 2
        assert options.allowed_hosts == []
        assert options.include_patterns == []
        assert options.exclude_patterns == []
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
                    links_found=0,
                )
            ],
        )

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        [
            "audit-technical",
            "https://example.com",
            "--max-pages",
            "25",
            "--max-depth",
            "2",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["start_url"] == "https://example.com/"
    assert data["findings"][0]["id"] == "technical.zero_links_found"
    assert data["summary"]["total_findings"] == 1


def test_cli_audit_technical_passes_noise_and_scope_options(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None):
        assert url == "https://example.com"
        assert options.max_pages == 10
        assert options.max_depth == 4
        assert options.allowed_hosts == ["example.com", "docs.example.com"]
        assert options.include_patterns == ["/docs/*"]
        assert options.exclude_patterns == ["/private/*"]
        return CrawlResult(start_url="https://example.com/", pages=[])

    def fake_technical_audit(inventory_result, options=None):
        assert inventory_result.start_url == "https://example.com/"
        assert options.max_depth_warning == 5
        assert options.high_skipped_urls_warning == 7
        assert options.flag_non_html is False
        assert options.flag_redirects is False
        assert options.flag_zero_links is False
        return TechnicalAuditResult(
            start_url=inventory_result.start_url,
            findings=[],
            summary=TechnicalAuditSummary(),
        )

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)
    monkeypatch.setattr(cli, "run_technical_audit", fake_technical_audit)

    result = runner.invoke(
        app,
        [
            "audit-technical",
            "https://example.com",
            "--max-pages",
            "10",
            "--max-depth",
            "4",
            "--max-depth-warning",
            "5",
            "--high-skipped-urls-warning",
            "7",
            "--no-non-html-findings",
            "--no-redirect-findings",
            "--no-zero-links-findings",
            "--allowed-host",
            "example.com",
            "--allowed-host",
            "docs.example.com",
            "--include-pattern",
            "/docs/*",
            "--exclude-pattern",
            "/private/*",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["summary"]["total_findings"] == 0


def test_cli_audit_technical_rejects_invalid_format(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None):
        raise AssertionError("crawl should not run for invalid format")

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        ["audit-technical", "https://example.com", "--format", "table"],
    )

    assert result.exit_code != 0
    assert "is not one of 'json'" in result.output.lower()
