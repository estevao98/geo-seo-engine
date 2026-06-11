from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import httpx


@dataclass
class SitemapEntry:
    loc: str
    lastmod: str | None


@dataclass
class SitemapAuditResult:
    url: str
    final_url: str
    status_code: int
    content_type: str | None
    sitemap_type: str | None
    url_count: int
    urls: list[SitemapEntry]
    duplicate_urls: list[str]
    invalid_urls: list[str]
    urls_with_query: list[str]
    off_domain_urls: list[str]
    missing_lastmod_count: int
    issues: list[str]


def _strip_namespace(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _child_text(element: ET.Element, child_name: str) -> str | None:
    for child in list(element):
        if _strip_namespace(child.tag) == child_name and child.text:
            return child.text.strip()
    return None


def audit_sitemap(url: str, timeout: float = 20.0) -> SitemapAuditResult:
    issues: list[str] = []

    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=timeout,
            headers={
                "User-Agent": "geo-seo-engine/0.1.0 (+https://example.com)"
            },
        )
    except httpx.HTTPError as exc:
        return SitemapAuditResult(
            url=url,
            final_url=url,
            status_code=0,
            content_type=None,
            sitemap_type=None,
            url_count=0,
            urls=[],
            duplicate_urls=[],
            invalid_urls=[],
            urls_with_query=[],
            off_domain_urls=[],
            missing_lastmod_count=0,
            issues=[f"request_error: {exc}"],
        )

    final_url = str(response.url)
    status_code = response.status_code
    content_type = response.headers.get("content-type")

    if status_code != 200:
        issues.append(f"status_code_not_200: {status_code}")

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as exc:
        return SitemapAuditResult(
            url=url,
            final_url=final_url,
            status_code=status_code,
            content_type=content_type,
            sitemap_type=None,
            url_count=0,
            urls=[],
            duplicate_urls=[],
            invalid_urls=[],
            urls_with_query=[],
            off_domain_urls=[],
            missing_lastmod_count=0,
            issues=issues + [f"xml_parse_error: {exc}"],
        )

    root_name = _strip_namespace(root.tag)
    if root_name not in {"urlset", "sitemapindex"}:
        issues.append(f"unexpected_root_element: {root_name}")

    entries: list[SitemapEntry] = []

    if root_name == "urlset":
        for url_el in list(root):
            if _strip_namespace(url_el.tag) != "url":
                continue
            loc = _child_text(url_el, "loc")
            lastmod = _child_text(url_el, "lastmod")
            if loc:
                entries.append(SitemapEntry(loc=loc, lastmod=lastmod))

    elif root_name == "sitemapindex":
        for sitemap_el in list(root):
            if _strip_namespace(sitemap_el.tag) != "sitemap":
                continue
            loc = _child_text(sitemap_el, "loc")
            lastmod = _child_text(sitemap_el, "lastmod")
            if loc:
                entries.append(SitemapEntry(loc=loc, lastmod=lastmod))

    seen: set[str] = set()
    duplicate_urls: list[str] = []
    invalid_urls: list[str] = []
    urls_with_query: list[str] = []
    off_domain_urls: list[str] = []

    sitemap_host = urlparse(final_url).netloc

    for entry in entries:
        parsed = urlparse(entry.loc)

        if not parsed.scheme or not parsed.netloc:
            invalid_urls.append(entry.loc)

        if parsed.query:
            urls_with_query.append(entry.loc)

        if parsed.netloc and sitemap_host and parsed.netloc != sitemap_host:
            off_domain_urls.append(entry.loc)

        if entry.loc in seen and entry.loc not in duplicate_urls:
            duplicate_urls.append(entry.loc)
        seen.add(entry.loc)

    missing_lastmod_count = sum(1 for entry in entries if not entry.lastmod)

    if not entries:
        issues.append("no_urls_found")

    if duplicate_urls:
        issues.append("duplicate_urls_found")

    if invalid_urls:
        issues.append("invalid_urls_found")

    if urls_with_query:
        issues.append("urls_with_query_found")

    if off_domain_urls:
        issues.append("off_domain_urls_found")

    return SitemapAuditResult(
        url=url,
        final_url=final_url,
        status_code=status_code,
        content_type=content_type,
        sitemap_type=root_name,
        url_count=len(entries),
        urls=entries,
        duplicate_urls=duplicate_urls,
        invalid_urls=invalid_urls,
        urls_with_query=urls_with_query,
        off_domain_urls=off_domain_urls,
        missing_lastmod_count=missing_lastmod_count,
        issues=issues,
    )
