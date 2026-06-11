from geo_seo_engine.analyzers.page_audit import PageAuditResult
from geo_seo_engine.analyzers.robots_audit import RobotsAuditResult
from geo_seo_engine.analyzers.sitemap_audit import SitemapAuditResult
from geo_seo_engine.analyzers.site_audit import SiteAuditResult
from geo_seo_engine.reporting.markdown import render_site_markdown


def test_render_site_markdown_contains_sections():
    result = SiteAuditResult(
        url="https://example.com",
        page=PageAuditResult(
            url="https://example.com",
            final_url="https://example.com",
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

    markdown = render_site_markdown(result)

    assert "# Site Audit Report" in markdown
    assert "## Page" in markdown
    assert "## Robots.txt" in markdown
    assert "## Sitemap" in markdown
    assert "`page.missing_meta_description`" in markdown
    assert "Critical issues" in markdown
    assert "**medium** — `page.missing_meta_description`" in markdown
    assert "## Recommendations" in markdown
    assert "**Ação:**" in markdown
