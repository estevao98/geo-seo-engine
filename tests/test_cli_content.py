import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app
from geo_seo_engine.crawler import CrawlResult, crawl_site
from geo_seo_engine.http import FetchResult

runner = CliRunner()


class FakeHttpClient:
    def __init__(self) -> None:
        self.requested_urls: list[str] = []

    def fetch(self, url: str) -> FetchResult:
        self.requested_urls.append(url)
        return FetchResult(
            url=url,
            final_url=url,
            status_code=200,
            content_type="text/html; charset=utf-8",
            text=(
                "<html><head><title>Guide</title>"
                '<meta name="description" content="Helpful guide.">'
                "</head><body><main>"
                "<h1>Useful guide</h1>"
                "<p>Useful crawl-time page copy for extraction.</p>"
                '<a href="/internal">Internal</a>'
                '<a href="https://external.example/page">External</a>'
                "</main></body></html>"
            ),
        )


def test_cli_extract_content_returns_valid_json_without_refetch(monkeypatch):
    import geo_seo_engine.cli as cli

    fake_http_client = FakeHttpClient()

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        assert url == "https://example.com"
        assert options.max_pages == 25
        assert options.max_depth == 0
        assert options.allowed_hosts == []
        assert options.include_patterns == []
        assert options.exclude_patterns == []
        assert callable(on_html_page)
        return crawl_site(
            url,
            options=options,
            http_client=fake_http_client,
            on_html_page=on_html_page,
        )

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        [
            "extract-content",
            "https://example.com",
            "--max-pages",
            "25",
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
    assert data["summary"]["pages_with_main_content"] == 1
    assert data["pages"][0]["title"] == "Guide"
    assert data["pages"][0]["meta_description"] == "Helpful guide."
    assert data["pages"][0]["main_selector"] == "main"
    assert data["pages"][0]["headings"][0]["text"] == "Useful guide"
    assert data["pages"][0]["internal_link_count"] == 1
    assert data["pages"][0]["external_link_count"] == 1
    assert fake_http_client.requested_urls == ["https://example.com/"]
    assert all("external.example" not in requested_url for requested_url in fake_http_client.requested_urls)


def test_cli_extract_content_passes_scope_options(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        assert options.max_pages == 10
        assert options.max_depth == 3
        assert options.allowed_hosts == ["example.com", "docs.example.com"]
        assert options.include_patterns == ["/docs/*"]
        assert options.exclude_patterns == ["/private/*"]
        assert callable(on_html_page)
        return CrawlResult(start_url="https://example.com/", pages=[])

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        [
            "extract-content",
            "https://example.com",
            "--max-pages",
            "10",
            "--max-depth",
            "3",
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
    assert json.loads(result.stdout)["summary"]["total_pages"] == 0


def test_cli_extract_content_rejects_invalid_format(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        raise AssertionError("crawl should not run for invalid format")

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(app, ["extract-content", "https://example.com", "--format", "table"])

    assert result.exit_code != 0
    assert "is not one of 'json'" in result.output.lower()
