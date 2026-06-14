import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app
from geo_seo_engine.crawler import CrawlPage, CrawlResult, DiscoveredLink

runner = CliRunner()


def test_cli_audit_internal_links_returns_valid_json_from_crawl(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None):
        assert url == "https://example.com"
        assert options.max_pages == 10
        assert options.max_depth == 2
        assert options.allowed_hosts == ["example.com"]
        return _crawl_result(start_url="https://example.com/")

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        [
            "audit-internal-links",
            "https://example.com",
            "--max-pages",
            "10",
            "--max-depth",
            "2",
            "--allowed-host",
            "example.com",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["start_url"] == "https://example.com/"
    assert data["summary"]["total_pages"] == 2
    assert data["summary"]["internal_edges"] == 1
    assert data["pages"][1]["inbound_internal_links"] == 1


def test_cli_audit_internal_links_reads_existing_crawl_json(tmp_path):
    crawl_file = tmp_path / "crawl.json"
    crawl_file.write_text(
        json.dumps(_crawl_result(start_url="https://example.com/").model_dump(mode="json")),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["audit-internal-links", "--input", str(crawl_file), "--format", "json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["summary"]["total_pages"] == 2
    assert data["summary"]["crawled_pages"] == 2


def test_cli_audit_internal_links_requires_url_or_input():
    result = runner.invoke(app, ["audit-internal-links", "--format", "json"])

    assert result.exit_code == 1
    assert "URL is required" in result.output


def test_cli_audit_internal_links_rejects_invalid_format(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None):
        raise AssertionError("crawl should not run for invalid format")

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(app, ["audit-internal-links", "https://example.com", "--format", "table"])

    assert result.exit_code != 0
    assert "is not one of 'json'" in result.output.lower()


def _crawl_result(start_url: str):
    return CrawlResult(
        start_url=start_url,
        pages=[
            CrawlPage(
                url="https://example.com/",
                normalized_url="https://example.com/",
                final_url="https://example.com/",
                status_code=200,
                depth=0,
                links_found=1,
            ),
            CrawlPage(
                url="https://example.com/about",
                normalized_url="https://example.com/about",
                final_url="https://example.com/about",
                status_code=200,
                depth=1,
                discovered_from="https://example.com/",
                links_found=0,
            ),
        ],
        discovered_urls=[
            DiscoveredLink(
                raw_href="/about",
                resolved_url="https://example.com/about",
                normalized_url="https://example.com/about",
                anchor_text="About",
                source_url="https://example.com/",
                depth=1,
            )
        ],
    )
