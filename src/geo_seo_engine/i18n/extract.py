from __future__ import annotations

from collections import Counter
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from geo_seo_engine.core import is_same_site, normalize_url, resolve_url, url_host
from geo_seo_engine.i18n.models import HreflangLink, PageHreflangInventory, SkippedHreflangLink


def extract_hreflang_from_html(
    html: str,
    page_url: str,
    allowed_hosts: list[str] | None = None,
) -> PageHreflangInventory:
    links: list[HreflangLink] = []
    skipped_links: list[SkippedHreflangLink] = []
    soup = BeautifulSoup(html, "html.parser")
    effective_allowed_hosts = allowed_hosts or _default_allowed_hosts(page_url)
    page_normalized_url = _normalize_or_original(page_url)
    head = soup.find("head")
    if head is None:
        return PageHreflangInventory(page_url=page_url)

    for tag in head.find_all("link"):
        rel_values = tag.get("rel") or []
        rel_tokens = {str(value).lower() for value in rel_values} if isinstance(rel_values, list) else {
            value.lower() for value in str(rel_values).split()
        }
        if "alternate" not in rel_tokens:
            continue

        raw_hreflang_value = tag.get("hreflang")
        raw_href_value = tag.get("href")
        raw_hreflang = str(raw_hreflang_value).strip() if raw_hreflang_value is not None else ""
        raw_href = str(raw_href_value).strip() if raw_href_value is not None else ""

        if not raw_hreflang:
            skipped_links.append(
                SkippedHreflangLink(
                    page_url=page_url,
                    reason="missing_hreflang",
                    raw_hreflang=raw_hreflang if raw_hreflang_value is not None else None,
                    raw_href=raw_href if raw_href_value is not None else None,
                )
            )
            continue
        if not raw_href:
            skipped_links.append(
                SkippedHreflangLink(
                    page_url=page_url,
                    reason="missing_href",
                    raw_hreflang=raw_hreflang,
                    raw_href=raw_href if raw_href_value is not None else None,
                )
            )
            continue

        normalized_hreflang, is_invalid_hreflang, is_x_default = normalize_hreflang(raw_hreflang)
        resolved_url, normalized_url, is_invalid_url, is_non_http = _resolve_and_normalize_href(raw_href, page_url)
        is_relative = _is_relative_href(raw_href)
        is_external = False if is_invalid_url else not is_same_site(normalized_url, effective_allowed_hosts)

        links.append(
            HreflangLink(
                page_url=page_url,
                raw_hreflang=raw_hreflang,
                normalized_hreflang=normalized_hreflang,
                raw_href=raw_href,
                resolved_url=resolved_url,
                normalized_url=normalized_url,
                is_self_reference=not is_invalid_url and normalized_url == page_normalized_url,
                is_x_default=is_x_default,
                is_relative=is_relative,
                is_external=is_external,
                is_invalid_url=is_invalid_url,
                is_invalid_hreflang=is_invalid_hreflang,
                is_non_http=is_non_http,
            )
        )

    return PageHreflangInventory(
        page_url=page_url,
        links=links,
        skipped_links=skipped_links,
        duplicates=_duplicates(links),
    )


def normalize_hreflang(value: str) -> tuple[str | None, bool, bool]:
    cleaned = value.strip()
    if cleaned.lower() == "x-default":
        return "x-default", False, True
    if "_" in cleaned:
        return None, True, False

    parts = cleaned.split("-")
    if len(parts) == 1:
        language = parts[0]
        if len(language) in {2, 3} and language.isalpha() and not language.isupper():
            return language.lower(), False, False
        return None, True, False
    if len(parts) == 2:
        language, region = parts
        if len(language) in {2, 3} and language.isalpha() and len(region) == 2 and region.isalpha():
            return f"{language.lower()}-{region.upper()}", False, False
    return None, True, False


def _resolve_and_normalize_href(raw_href: str, page_url: str) -> tuple[str, str, bool, bool]:
    try:
        resolved_url = resolve_url(raw_href, page_url)
    except ValueError:
        return raw_href, raw_href, True, _has_non_http_scheme(raw_href)

    try:
        normalized = normalize_url(resolved_url)
    except ValueError:
        return resolved_url, resolved_url, True, _has_non_http_scheme(resolved_url)
    return resolved_url, normalized.normalized_url, False, False


def _is_relative_href(raw_href: str) -> bool:
    parts = urlsplit(raw_href)
    return not parts.scheme and not parts.netloc


def _has_non_http_scheme(url: str) -> bool:
    scheme = urlsplit(url).scheme.lower()
    return bool(scheme and scheme not in {"http", "https"})


def _default_allowed_hosts(page_url: str) -> list[str]:
    host = url_host(page_url)
    return [host] if host else []


def _normalize_or_original(url: str) -> str:
    try:
        return normalize_url(url).normalized_url
    except ValueError:
        return url


def _duplicates(links: list[HreflangLink]) -> dict[str, int]:
    counts = Counter(link.normalized_hreflang for link in links if link.normalized_hreflang)
    return dict(sorted((hreflang, count) for hreflang, count in counts.items() if count > 1))
