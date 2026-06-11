import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app

runner = CliRunner()


def test_audit_sitemap_json_output(monkeypatch):
    from geo_seo_engine.analyzers.sitemap_audit import SitemapAuditResult
    import geo_seo_engine.cli as cli

    def fake_audit_sitemap(url: str):
        return SitemapAuditResult(
            url=url,
            final_url=url,
            status_code=200,
            content_type="application/xml",
            sitemap_type="urlset",
            url_count=1,
            urls=[],
            duplicate_urls=[],
            invalid_urls=[],
            urls_with_query=[],
            off_domain_urls=[],
            missing_lastmod_count=0,
            issues=[],
        )

    monkeypatch.setattr(cli, "run_sitemap_audit", fake_audit_sitemap)

    result = runner.invoke(
        app,
        ["audit-sitemap", "https://example.com/sitemap.xml", "--format", "json"],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["url"] == "https://example.com/sitemap.xml"
    assert data["sitemap_type"] == "urlset"
    assert data["url_count"] == 1


def test_audit_sitemap_table_output_is_not_duplicated(monkeypatch):
    from geo_seo_engine.analyzers.sitemap_audit import SitemapAuditResult
    import geo_seo_engine.cli as cli

    def fake_audit_sitemap(url: str):
        return SitemapAuditResult(
            url=url,
            final_url=url,
            status_code=200,
            content_type="application/xml",
            sitemap_type="urlset",
            url_count=1,
            urls=[],
            duplicate_urls=[],
            invalid_urls=[],
            urls_with_query=[],
            off_domain_urls=[],
            missing_lastmod_count=0,
            issues=[],
        )

    monkeypatch.setattr(cli, "run_sitemap_audit", fake_audit_sitemap)

    result = runner.invoke(
        app,
        ["audit-sitemap", "https://example.com/sitemap.xml"],
    )

    assert result.exit_code == 0
    assert result.stdout.count("Sitemap Audit") == 1
