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
                '<html><body><img src="/logo.png" alt="Logo" width="10" height="10">'
                '<img src="/image.jpg" alt="Image" width="20" height="20"></body></html>'
            ),
        )


def test_cli_audit_images_returns_valid_json(monkeypatch):
    import geo_seo_engine.cli as cli

    fake_http_client = FakeHttpClient()

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        assert url == "https://example.com"
        assert options.max_pages == 25
        assert options.max_depth == 2
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
            "audit-images",
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
    assert data["summary"]["total_images"] == 2
    assert data["summary"]["findings_total"] == 0
    assert data["pages"][0]["images"][0]["normalized_src"] == "https://example.com/logo.png"
    assert fake_http_client.requested_urls == ["https://example.com/"]
    assert all("/logo.png" not in requested_url for requested_url in fake_http_client.requested_urls)
    assert all("/image.jpg" not in requested_url for requested_url in fake_http_client.requested_urls)


def test_cli_audit_images_passes_scope_options(monkeypatch):
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
            "audit-images",
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


def test_cli_audit_images_rejects_invalid_format(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None):
        raise AssertionError("crawl should not run for invalid format")

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        ["audit-images", "https://example.com", "--format", "table"],
    )

    assert result.exit_code != 0
    assert "is not one of 'json'" in result.output.lower()
