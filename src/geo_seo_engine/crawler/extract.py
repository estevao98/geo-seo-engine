from __future__ import annotations

import re
from fnmatch import fnmatch
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from geo_seo_engine.content import extract_main_content_from_html
from geo_seo_engine.core import is_same_site, normalize_url, resolve_url
from geo_seo_engine.crawler.models import DiscoveredLink, MainContent, SkippedUrl

_IGNORED_SCHEMES = {"mailto", "tel", "javascript", "data", "ftp"}


def extract_links(
    html: str,
    source_url: str,
    allowed_hosts: list[str],
    *,
    source_depth: int = 0,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> tuple[list[DiscoveredLink], list[SkippedUrl]]:
    links: list[DiscoveredLink] = []
    skipped: list[SkippedUrl] = []
    includes = include_patterns or []
    excludes = exclude_patterns or []
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all("a"):
        raw_href = str(tag.get("href") or "").strip()
        if not raw_href:
            skipped.append(SkippedUrl(url=raw_href, reason="empty_href", source_url=source_url))
            continue
        if raw_href.startswith("#"):
            skipped.append(SkippedUrl(url=raw_href, reason="fragment_only", source_url=source_url))
            continue

        scheme = urlsplit(raw_href).scheme.lower()
        if scheme in _IGNORED_SCHEMES:
            skipped.append(
                SkippedUrl(url=raw_href, reason=f"unsupported_scheme:{scheme}", source_url=source_url)
            )
            continue

        try:
            resolved_url = resolve_url(raw_href, source_url)
            normalized = normalize_url(resolved_url)
        except ValueError:
            skipped.append(SkippedUrl(url=raw_href, reason="invalid_url", source_url=source_url))
            continue

        if not is_same_site(normalized.normalized_url, allowed_hosts):
            skipped.append(
                SkippedUrl(
                    url=normalized.normalized_url,
                    reason="external_host",
                    source_url=source_url,
                )
            )
            continue

        if _matches_any(normalized.normalized_url, normalized.path, excludes):
            skipped.append(
                SkippedUrl(
                    url=normalized.normalized_url,
                    reason="excluded_by_pattern",
                    source_url=source_url,
                )
            )
            continue

        if includes and not _matches_any(normalized.normalized_url, normalized.path, includes):
            skipped.append(
                SkippedUrl(
                    url=normalized.normalized_url,
                    reason="not_included_by_pattern",
                    source_url=source_url,
                )
            )
            continue

        anchor_text = " ".join(tag.get_text(" ", strip=True).split()) or None
        links.append(
            DiscoveredLink(
                raw_href=raw_href,
                resolved_url=resolved_url,
                normalized_url=normalized.normalized_url,
                anchor_text=anchor_text,
                source_url=source_url,
                depth=source_depth + 1,
            )
        )

    return links, skipped


def extract_main_content(html: str) -> MainContent:
    extracted = extract_main_content_from_html(html, page_url="https://example.invalid/")
    return _main_content_from_text(extracted.plain_text, extracted.main_selector)


def _matches_any(normalized_url: str, path: str, patterns: list[str]) -> bool:
    return any(fnmatch(normalized_url, pattern) or fnmatch(path, pattern) for pattern in patterns)


def _main_content_from_text(text: str, selector: str | None) -> MainContent:
    return MainContent(
        selector=selector,
        text=text,
        text_length=len(text),
        word_count=len(re.findall(r"\b[\w'-]+\b", text)),
    )


def _clean_text(text: str) -> str:
    return " ".join(text.split())
