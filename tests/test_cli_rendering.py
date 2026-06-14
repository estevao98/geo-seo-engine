import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app
from geo_seo_engine.crawler import CrawlPage, CrawlResult

runner = CliRunner()


def test_cli_audit_rendering_fails_without_renderer(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        raise AssertionError("crawl should not run without a renderer")

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(app, ["audit-rendering", "https://example.com", "--format", "json"])

    assert result.exit_code == 1
    assert "No JavaScript renderer is configured" in result.stderr


def test_cli_audit_rendering_returns_json_with_static_renderer(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        assert options.max_pages == 1
        assert options.max_depth == 0
        assert on_html_page is not None
        html = "<html><head><title>Static</title></head><body><a href='/a'>A</a>Static content</body></html>"
        on_html_page(
            page_url=url,
            normalized_url="https://example.com/",
            final_url="https://example.com/",
            html=html,
            content_type="text/html",
            depth=0,
        )
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
                    links_found=1,
                )
            ],
        )

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        [
            "audit-rendering",
            "https://example.com",
            "--renderer",
            "static",
            "--max-pages",
            "1",
            "--max-depth",
            "0",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["start_url"] == "https://example.com/"
    assert data["summary"]["total_pages"] == 1
    assert data["summary"]["rendered_pages"] == 1
    assert data["summary"]["findings_total"] == 0
    assert data["pages"][0]["render_status"] == "rendered"
