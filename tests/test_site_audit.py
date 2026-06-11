from geo_seo_engine.analyzers.page_audit import PageAuditResult
from geo_seo_engine.analyzers.robots_audit import RobotsAuditResult
from geo_seo_engine.analyzers.sitemap_audit import SitemapAuditResult
from geo_seo_engine.analyzers.structured_data_audit import StructuredDataAuditResult
from geo_seo_engine.analyzers.site_audit import audit_site

import geo_seo_engine.analyzers.site_audit as site_audit_module


def test_audit_site_uses_sitemap_from_robots(monkeypatch):
    def fake_audit_page(url: str):
        return PageAuditResult(
            url=url,
            final_url=url,
            status_code=200,
            title="Title",
            meta_description="Description",
            h1=["H1"],
            canonical=url,
            meta_robots=None,
            noindex=False,
            internal_links=1,
            external_links=1,
            issues=[],
        )

    def fake_audit_robots(url: str):
        return RobotsAuditResult(
            url="https://example.com/robots.txt",
            final_url="https://example.com/robots.txt",
            status_code=200,
            content_type="text/plain",
            line_count=3,
            user_agents=["*"],
            allow_count=0,
            disallow_count=0,
            sitemap_urls=["https://example.com/custom-sitemap.xml"],
            crawl_delay_count=0,
            unknown_directives=[],
            blocks_all=False,
            issues=[],
        )

    def fake_audit_sitemap(url: str):
        assert url == "https://example.com/custom-sitemap.xml"
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

    def fake_audit_structured_data(url: str):
        return StructuredDataAuditResult(
            json_ld_blocks=1,
            valid_json_ld_blocks=1,
            invalid_json_ld_blocks=0,
            types=["WebSite"],
            blocks=[],
            issues=[],
        )

    monkeypatch.setattr(site_audit_module, "audit_page", fake_audit_page)
    monkeypatch.setattr(site_audit_module, "audit_robots", fake_audit_robots)
    monkeypatch.setattr(site_audit_module, "audit_sitemap", fake_audit_sitemap)
    monkeypatch.setattr(
        site_audit_module, "audit_structured_data", fake_audit_structured_data
    )

    result = audit_site("https://example.com")

    assert result.page.status_code == 200
    assert result.robots.sitemap_urls == ["https://example.com/custom-sitemap.xml"]
    assert result.sitemap.url_count == 1
    assert result.structured_data.types == ["WebSite"]
    assert result.issues == []
    assert result.score == 100
    assert result.next_action is None


def test_audit_site_prefixes_issues(monkeypatch):
    def fake_audit_page(url: str):
        return PageAuditResult(
            url=url,
            final_url=url,
            status_code=200,
            title=None,
            meta_description=None,
            h1=[],
            canonical=None,
            meta_robots=None,
            noindex=False,
            internal_links=0,
            external_links=0,
            issues=["missing_title"],
        )

    def fake_audit_robots(url: str):
        return RobotsAuditResult(
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
            blocks_all=True,
            issues=["disallow_all_found"],
        )

    def fake_audit_sitemap(url: str):
        return SitemapAuditResult(
            url=url,
            final_url=url,
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
            issues=["xml_parse_error"],
        )

    def fake_audit_structured_data(url: str):
        return StructuredDataAuditResult(
            json_ld_blocks=0,
            valid_json_ld_blocks=0,
            invalid_json_ld_blocks=0,
            types=[],
            blocks=[],
            issues=["missing"],
        )

    monkeypatch.setattr(site_audit_module, "audit_page", fake_audit_page)
    monkeypatch.setattr(site_audit_module, "audit_robots", fake_audit_robots)
    monkeypatch.setattr(site_audit_module, "audit_sitemap", fake_audit_sitemap)
    monkeypatch.setattr(
        site_audit_module, "audit_structured_data", fake_audit_structured_data
    )

    result = audit_site("https://example.com")

    assert result.issues == [
        "page.missing_title",
        "robots.disallow_all_found",
        "sitemap.xml_parse_error",
        "structured_data.missing",
    ]
    assert result.score == 41
    assert result.next_action == (
        "Revisar o Disallow: / e remover o bloqueio se páginas públicas devem ser rastreadas."
    )
