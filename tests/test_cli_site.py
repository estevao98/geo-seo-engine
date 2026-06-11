import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app

runner = CliRunner()


def test_audit_site_json_output(monkeypatch):
    from geo_seo_engine.analyzers.page_audit import PageAuditResult
    from geo_seo_engine.analyzers.robots_audit import RobotsAuditResult
    from geo_seo_engine.analyzers.sitemap_audit import SitemapAuditResult
    from geo_seo_engine.analyzers.site_audit import SiteAuditResult
    import geo_seo_engine.cli as cli

    def fake_audit_site(url: str, sitemap_url=None):
        return SiteAuditResult(
            url=url,
            page=PageAuditResult(
                url=url,
                final_url=url,
                status_code=200,
                title="Title",
                meta_description=None,
                h1=["H1"],
                canonical=None,
                meta_robots=None,
                noindex=False,
                internal_links=1,
                external_links=1,
                issues=[],
            ),
            robots=RobotsAuditResult(
                url="https://example.com/robots.txt",
                final_url="https://example.com/robots.txt",
                status_code=200,
                content_type="text/plain",
                line_count=1,
                user_agents=["*"],
                allow_count=0,
                disallow_count=0,
                sitemap_urls=[],
                crawl_delay_count=0,
                unknown_directives=[],
                blocks_all=False,
                issues=[],
            ),
            sitemap=SitemapAuditResult(
                url="https://example.com/sitemap.xml",
                final_url="https://example.com/sitemap.xml",
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
            ),
            issues=[],
        )

    monkeypatch.setattr(cli, "run_site_audit", fake_audit_site)

    result = runner.invoke(
        app,
        ["audit-site", "https://example.com", "--format", "json"],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["url"] == "https://example.com"
    assert data["page"]["status_code"] == 200
    assert data["robots"]["status_code"] == 200
    assert data["sitemap"]["url_count"] == 1
    assert data["score"] == 100


def test_audit_site_table_output_is_not_duplicated(monkeypatch):
    from geo_seo_engine.analyzers.page_audit import PageAuditResult
    from geo_seo_engine.analyzers.robots_audit import RobotsAuditResult
    from geo_seo_engine.analyzers.sitemap_audit import SitemapAuditResult
    from geo_seo_engine.analyzers.site_audit import SiteAuditResult
    import geo_seo_engine.cli as cli

    def fake_audit_site(url: str, sitemap_url=None):
        return SiteAuditResult(
            url=url,
            page=PageAuditResult(
                url=url,
                final_url=url,
                status_code=200,
                title="Title",
                meta_description=None,
                h1=["H1"],
                canonical=None,
                meta_robots=None,
                noindex=False,
                internal_links=1,
                external_links=1,
                issues=[],
            ),
            robots=RobotsAuditResult(
                url="https://example.com/robots.txt",
                final_url="https://example.com/robots.txt",
                status_code=200,
                content_type="text/plain",
                line_count=1,
                user_agents=["*"],
                allow_count=0,
                disallow_count=0,
                sitemap_urls=[],
                crawl_delay_count=0,
                unknown_directives=[],
                blocks_all=False,
                issues=[],
            ),
            sitemap=SitemapAuditResult(
                url="https://example.com/sitemap.xml",
                final_url="https://example.com/sitemap.xml",
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
            ),
            issues=[],
        )

    monkeypatch.setattr(cli, "run_site_audit", fake_audit_site)

    result = runner.invoke(app, ["audit-site", "https://example.com"])

    assert result.exit_code == 0
    assert result.stdout.count("Site Audit") == 1


def test_audit_site_markdown_output(monkeypatch):
    from geo_seo_engine.analyzers.page_audit import PageAuditResult
    from geo_seo_engine.analyzers.robots_audit import RobotsAuditResult
    from geo_seo_engine.analyzers.sitemap_audit import SitemapAuditResult
    from geo_seo_engine.analyzers.site_audit import SiteAuditResult
    import geo_seo_engine.cli as cli

    def fake_audit_site(url: str, sitemap_url=None):
        return SiteAuditResult(
            url=url,
            page=PageAuditResult(
                url=url,
                final_url=url,
                status_code=200,
                title="Title",
                meta_description=None,
                h1=["H1"],
                canonical=None,
                meta_robots=None,
                noindex=False,
                internal_links=1,
                external_links=1,
                issues=["missing_meta_description"],
            ),
            robots=RobotsAuditResult(
                url="https://example.com/robots.txt",
                final_url="https://example.com/robots.txt",
                status_code=404,
                content_type="text/html",
                line_count=0,
                user_agents=[],
                allow_count=0,
                disallow_count=0,
                sitemap_urls=[],
                crawl_delay_count=0,
                unknown_directives=[],
                blocks_all=False,
                issues=["status_code_not_200: 404"],
            ),
            sitemap=SitemapAuditResult(
                url="https://example.com/sitemap.xml",
                final_url="https://example.com/sitemap.xml",
                status_code=404,
                content_type="text/html",
                sitemap_type=None,
                url_count=0,
                urls=[],
                duplicate_urls=[],
                invalid_urls=[],
                urls_with_query=[],
                off_domain_urls=[],
                missing_lastmod_count=0,
                issues=["status_code_not_200: 404"],
            ),
            issues=[
                "page.missing_meta_description",
                "robots.status_code_not_200: 404",
                "sitemap.status_code_not_200: 404",
            ],
        )

    monkeypatch.setattr(cli, "run_site_audit", fake_audit_site)

    result = runner.invoke(
        app,
        ["audit-site", "https://example.com", "--format", "markdown"],
    )

    assert result.exit_code == 0
    assert "# Site Audit Report" in result.stdout
    assert "## Page" in result.stdout
    assert "## Robots.txt" in result.stdout
    assert "## Sitemap" in result.stdout
    assert "`page.missing_meta_description`" in result.stdout
