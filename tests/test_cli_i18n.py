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
        path = "/pt-br/" if url.endswith("/pt-br/") else "/en/"
        hreflang = "pt-BR" if path == "/pt-br/" else "en"
        other_path = "/en/" if path == "/pt-br/" else "/pt-br/"
        other_hreflang = "en" if path == "/pt-br/" else "pt-BR"
        return FetchResult(
            url=url,
            final_url=url,
            status_code=200,
            content_type="text/html; charset=utf-8",
            text=(
                "<html><head>"
                f'<link rel="alternate" hreflang="{hreflang}" href="https://example.com{path}">'
                f'<link rel="alternate" hreflang="{other_hreflang}" href="https://example.com{other_path}">'
                '<link rel="alternate" hreflang="fr" href="https://example.com/fr/">'
                "</head><body>"
                '<a href="/pt-br/">PT</a>'
                "</body></html>"
            ),
        )


def test_cli_audit_hreflang_returns_valid_json(monkeypatch):
    import geo_seo_engine.cli as cli

    fake_http_client = FakeHttpClient()

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        assert url == "https://example.com/en/"
        assert options.max_pages == 2
        assert options.max_depth == 1
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
            "audit-hreflang",
            "https://example.com/en/",
            "--max-pages",
            "2",
            "--max-depth",
            "1",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["start_url"] == "https://example.com/en/"
    assert data["summary"]["total_pages"] == 2
    assert data["summary"]["total_links"] == 6
    assert data["summary"]["missing_reciprocal_links"] == 0
    assert fake_http_client.requested_urls == ["https://example.com/en/", "https://example.com/pt-br/"]
    assert "https://example.com/fr/" not in fake_http_client.requested_urls


def test_cli_audit_hreflang_passes_scope_options(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        assert options.max_pages == 10
        assert options.max_depth == 3
        assert options.allowed_hosts == ["example.com", "example.fr"]
        assert options.include_patterns == ["/docs/*"]
        assert options.exclude_patterns == ["/private/*"]
        assert callable(on_html_page)
        return CrawlResult(start_url="https://example.com/", pages=[])

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        [
            "audit-hreflang",
            "https://example.com",
            "--max-pages",
            "10",
            "--max-depth",
            "3",
            "--allowed-host",
            "example.com",
            "--allowed-host",
            "example.fr",
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


def test_cli_audit_hreflang_rejects_invalid_format(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        raise AssertionError("crawl should not run for invalid format")

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(app, ["audit-hreflang", "https://example.com", "--format", "table"])

    assert result.exit_code != 0
    assert "is not one of 'json'" in result.output.lower()
