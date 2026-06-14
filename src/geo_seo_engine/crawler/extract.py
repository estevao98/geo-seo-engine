from __future__ import annotations

import re
from fnmatch import fnmatch
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from geo_seo_engine.core import is_same_site, normalize_url, resolve_url
from geo_seo_engine.crawler.models import DiscoveredLink, MainContent, SkippedUrl

_IGNORED_SCHEMES = {"mailto", "tel", "javascript", "data", "ftp"}
_MAIN_CONTENT_SELECTORS = "main, article, [role='main']"
_NON_CONTENT_SELECTORS = "script, style, noscript, svg, template, nav, header, footer, aside, form, dialog"
_HIDDEN_SELECTORS = "[hidden], [aria-hidden='true']"


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
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.select(_NON_CONTENT_SELECTORS):
        tag.decompose()
    for tag in soup.select(_HIDDEN_SELECTORS):
        tag.decompose()

    candidates = soup.select(_MAIN_CONTENT_SELECTORS)
    if not candidates:
        fallback = soup.body or soup
        text = _clean_text(fallback.get_text(" "))
        return _main_content_from_text(text, _selector_for(fallback))

    best_candidate = max(candidates, key=lambda tag: len(_clean_text(tag.get_text(" "))))
    text = _clean_text(best_candidate.get_text(" "))
    return _main_content_from_text(text, _selector_for(best_candidate))


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


def _selector_for(tag) -> str | None:
    name = getattr(tag, "name", None)
    if not name or name == "[document]":
        return None

    tag_id = tag.get("id")
    if tag_id:
        return f"{name}#{tag_id}"

    classes = tag.get("class") or []
    if classes:
        return f"{name}.{classes[0]}"

    role = tag.get("role")
    if role:
        return f"{name}[role='{role}']"

    return name
