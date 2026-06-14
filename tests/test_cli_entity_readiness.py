import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app

runner = CliRunner()


def test_cli_audit_entity_readiness_reads_local_html_file(tmp_path):
    html_file = tmp_path / "page.html"
    html_file.write_text(
        """
        <html>
          <head>
            <title>Entity SEO Guide</title>
            <meta name="description" content="Entity SEO guide for SaaS teams.">
            <script type="application/ld+json">
            {"@context":"https://schema.org","@type":"Article","author":{"@type":"Person","name":"Ana Silva"},"publisher":{"@type":"Organization","name":"Acme","sameAs":"https://example.com/acme"}}
            </script>
          </head>
          <body><main><p class="byline">Written by Ana Silva</p><h1>Entity SEO Guide</h1>
            <p>Entity SEO guide content helps SaaS teams clarify topics, authors and publishers.</p>
            <p>Entity signals include title, headings, metadata, author names and organization names.</p>
          </main></body>
        </html>
        """,
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "audit-entity-readiness",
            "https://example.com/entity-guide",
            "--html-file",
            str(html_file),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["start_url"] == "https://example.com/entity-guide"
    assert data["summary"]["total_pages"] == 1
    assert data["page_audits"][0]["structured_data"]["has_article"] is True
    assert data["summary"]["pages_with_author_signal"] == 1


def test_cli_audit_entity_readiness_passes_crawl_scope_options(monkeypatch):
    import geo_seo_engine.cli as cli

    def fake_crawl_site(url: str, options=None, on_html_page=None):
        assert url == "https://example.com"
        assert options.max_pages == 7
        assert options.max_depth == 1
        assert options.allowed_hosts == ["example.com"]
        assert options.include_patterns == ["/guides/*"]
        assert options.exclude_patterns == ["/private/*"]
        assert callable(on_html_page)
        on_html_page(
            page_url="https://example.com/",
            normalized_url="https://example.com/",
            final_url="https://example.com/",
            html="<main><h1>Guide</h1><p>Guide content about entities and publishers for teams.</p></main>",
            content_type="text/html",
            depth=0,
        )

        class CrawlResult:
            start_url = "https://example.com/"

        return CrawlResult()

    monkeypatch.setattr(cli, "run_crawl_site", fake_crawl_site)

    result = runner.invoke(
        app,
        [
            "audit-entity-readiness",
            "https://example.com",
            "--max-pages",
            "7",
            "--max-depth",
            "1",
            "--allowed-host",
            "example.com",
            "--include-pattern",
            "/guides/*",
            "--exclude-pattern",
            "/private/*",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["summary"]["total_pages"] == 1
