import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app
from geo_seo_engine.crawler import CrawlResult

runner = CliRunner()


def test_cli_audit_social_returns_valid_json(monkeypatch):
    import geo_seo_engine.cli as cli

    calls = []

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        assert url == "https://example.com"
        assert options.max_pages == 25
        assert options.max_depth == 2
        assert callable(on_html_page)
        calls.append(url)
        on_html_page(
            page_url="https://example.com/",
            normalized_url="https://example.com/",
            final_url="https://example.com/",
            html=(
                '<meta property="og:title" content="Title">'
                '<meta property="og:description" content="Description">'
                '<meta property="og:image" content="https://example.com/social.png">'
                '<meta property="og:url" content="https://example.com/">'
                '<meta name="twitter:card" content="summary_large_image">'
            ),
            content_type="text/html; charset=utf-8",
            depth=0,
        )
        return CrawlResult(start_url="https://example.com/", pages=[])

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        [
            "audit-social",
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
    assert data["summary"]["total_pages"] == 1
    assert data["pages"][0]["open_graph"]["og:title"] == "Title"
    assert calls == ["https://example.com"]
    assert all("social.png" not in requested_url for requested_url in calls)


def test_cli_audit_social_rejects_invalid_format(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        raise AssertionError("crawl should not run for invalid format")

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        ["audit-social", "https://example.com", "--format", "table"],
    )

    assert result.exit_code != 0
    assert "is not one of 'json'" in result.output.lower()


def test_cli_audit_social_passes_scope_options(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        assert options.max_pages == 10
        assert options.max_depth == 3
        assert options.allowed_hosts == ["example.com", "cdn.example.com"]
        assert options.include_patterns == ["/docs/*"]
        assert options.exclude_patterns == ["/private/*"]
        assert callable(on_html_page)
        return CrawlResult(start_url="https://example.com/", pages=[])

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        [
            "audit-social",
            "https://example.com",
            "--max-pages",
            "10",
            "--max-depth",
            "3",
            "--allowed-host",
            "example.com",
            "--allowed-host",
            "cdn.example.com",
            "--include-pattern",
            "/docs/*",
            "--exclude-pattern",
            "/private/*",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["summary"]["total_pages"] == 0


def test_cli_audit_social_uses_on_html_page_without_refetching(monkeypatch):
    import geo_seo_engine.cli as cli

    state = {"callback_called": False, "extract_calls": 0}
    original_extract = cli.extract_social_metadata_from_html

    def fake_extract_social_metadata_from_html(html: str, page_url: str, allowed_hosts=None):
        state["extract_calls"] += 1
        assert html == '<meta property="og:title" content="Title">'
        assert page_url == "https://example.com/final"
        return original_extract(html, page_url, allowed_hosts=allowed_hosts)

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        assert callable(on_html_page)
        state["callback_called"] = True
        on_html_page(
            page_url="https://example.com/page",
            normalized_url="https://example.com/page",
            final_url="https://example.com/final",
            html='<meta property="og:title" content="Title">',
            content_type="text/html",
            depth=0,
        )
        return CrawlResult(start_url="https://example.com/", pages=[])

    monkeypatch.setattr(cli, "extract_social_metadata_from_html", fake_extract_social_metadata_from_html)
    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(app, ["audit-social", "https://example.com", "--format", "json"])

    assert result.exit_code == 0
    assert state == {"callback_called": True, "extract_calls": 1}
