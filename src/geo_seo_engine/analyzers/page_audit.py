from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass
class PageAuditResult:
    url: str
    final_url: str
    status_code: int
    title: str | None
    meta_description: str | None
    h1: list[str]
    canonical: str | None
    meta_robots: str | None
    noindex: bool
    internal_links: int
    external_links: int
    issues: list[str]


def _get_attr(soup: BeautifulSoup, selector: str, attr: str) -> str | None:
    tag = soup.select_one(selector)
    if not tag:
        return None
    value = tag.get(attr)
    if not value:
        return None
    return str(value).strip()


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split()).strip()
    return cleaned or None


def audit_page(url: str, timeout: float = 15.0) -> PageAuditResult:
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
        return PageAuditResult(
            url=url,
            final_url=url,
            status_code=0,
            title=None,
            meta_description=None,
            h1=[],
            canonical=None,
            meta_robots=None,
            noindex=False,
            internal_links=0,
            external_links=0,
            issues=[f"request_error: {exc}"],
        )

    final_url = str(response.url)
    status_code = response.status_code

    if status_code != 200:
        issues.append(f"status_code_not_200: {status_code}")

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        issues.append(f"non_html_content_type: {content_type}")

    soup = BeautifulSoup(response.text, "html.parser")

    title = _clean_text(soup.title.string if soup.title and soup.title.string else None)
    meta_description = _clean_text(
        _get_attr(soup, 'meta[name="description"]', "content")
    )
    canonical = _get_attr(soup, 'link[rel="canonical"]', "href")
    meta_robots = _get_attr(soup, 'meta[name="robots"]', "content")

    h1 = [
        text
        for text in (_clean_text(tag.get_text(" ", strip=True)) for tag in soup.find_all("h1"))
        if text
    ]

    robots_lower = (meta_robots or "").lower()
    noindex = "noindex" in robots_lower

    if noindex:
        issues.append("meta_robots_noindex")

    if not title:
        issues.append("missing_title")

    if not meta_description:
        issues.append("missing_meta_description")

    if not h1:
        issues.append("missing_h1")

    if len(h1) > 1:
        issues.append("multiple_h1")

    if not canonical:
        issues.append("missing_canonical")

    page_host = urlparse(final_url).netloc
    internal_links = 0
    external_links = 0

    for a in soup.find_all("a", href=True):
        href = str(a.get("href", "")).strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        parsed = urlparse(href)
        if not parsed.netloc or parsed.netloc == page_host:
            internal_links += 1
        else:
            external_links += 1

    return PageAuditResult(
        url=url,
        final_url=final_url,
        status_code=status_code,
        title=title,
        meta_description=meta_description,
        h1=h1,
        canonical=canonical,
        meta_robots=meta_robots,
        noindex=noindex,
        internal_links=internal_links,
        external_links=external_links,
        issues=issues,
    )
