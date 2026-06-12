import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app
from geo_seo_engine.crawler import CrawlPage, CrawlResult

runner = CliRunner()


def test_cli_inventory_returns_valid_json(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None):
        assert url == "https://example.com"
        assert options.max_pages == 25
        assert options.max_depth == 2
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
                )
            ],
        )

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        ["inventory", "https://example.com", "--max-pages", "25", "--max-depth", "2", "--format", "json"],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["start_url"] == "https://example.com/"
    assert data["urls"][0]["status_code"] == 200
    assert data["urls"][0]["is_html"] is True
    assert data["summary"]["total_pages"] == 1


def test_cli_inventory_rejects_invalid_format(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None):
        raise AssertionError("crawl should not run for invalid format")

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(app, ["inventory", "https://example.com", "--format", "table"])

    assert result.exit_code != 0
    assert "is not one of 'json'" in result.output.lower()
