from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from geo_seo_engine.analyzers.page_audit import PageAuditResult, audit_page
from geo_seo_engine.analyzers.robots_audit import RobotsAuditResult, audit_robots
from geo_seo_engine.analyzers.sitemap_audit import SitemapAuditResult, audit_sitemap


@dataclass
class SiteAuditResult:
    url: str
    page: PageAuditResult
    robots: RobotsAuditResult
    sitemap: SitemapAuditResult
    issues: list[str]


def _default_sitemap_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    return f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"


def audit_site(url: str, sitemap_url: str | None = None) -> SiteAuditResult:
    page_result = audit_page(url)
    robots_result = audit_robots(url)

    selected_sitemap_url = (
        sitemap_url
        or (robots_result.sitemap_urls[0] if robots_result.sitemap_urls else None)
        or _default_sitemap_url(url)
    )

    sitemap_result = audit_sitemap(selected_sitemap_url)

    issues: list[str] = []

    for issue in page_result.issues:
        issues.append(f"page.{issue}")

    for issue in robots_result.issues:
        issues.append(f"robots.{issue}")

    for issue in sitemap_result.issues:
        issues.append(f"sitemap.{issue}")

    return SiteAuditResult(
        url=url,
        page=page_result,
        robots=robots_result,
        sitemap=sitemap_result,
        issues=issues,
    )
