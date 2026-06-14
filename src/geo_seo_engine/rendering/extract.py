from __future__ import annotations

from bs4 import BeautifulSoup

from geo_seo_engine.core import normalize_url, resolve_url
from geo_seo_engine.rendering.models import PageRenderSnapshot, RenderStatus


def extract_render_snapshot(
    page_url: str,
    static_html: str,
    rendered_html: str | None = None,
    render_error: str | None = None,
    render_status: RenderStatus | None = None,
) -> PageRenderSnapshot:
    static_doc = _extract_document_signals(static_html, page_url)
    rendered_doc = _extract_document_signals(rendered_html or "", page_url) if rendered_html is not None else None
    status = render_status or ("error" if render_error else "rendered")

    return PageRenderSnapshot(
        page_url=page_url,
        static_html=static_html,
        rendered_html=rendered_html,
        static_title=static_doc["title"],
        rendered_title=rendered_doc["title"] if rendered_doc else None,
        static_meta_description=static_doc["meta_description"],
        rendered_meta_description=rendered_doc["meta_description"] if rendered_doc else None,
        static_canonical=static_doc["canonical"],
        rendered_canonical=rendered_doc["canonical"] if rendered_doc else None,
        static_robots=static_doc["robots"],
        rendered_robots=rendered_doc["robots"] if rendered_doc else None,
        static_links=static_doc["links"],
        rendered_links=rendered_doc["links"] if rendered_doc else [],
        static_text_length=static_doc["text_length"],
        rendered_text_length=rendered_doc["text_length"] if rendered_doc else 0,
        static_script_count=static_doc["script_count"],
        render_status=status,
        render_error=render_error,
    )


def _extract_document_signals(html: str, page_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    description_tag = soup.find("meta", attrs={"name": _case_insensitive_value("description")})
    robots_tag = soup.find("meta", attrs={"name": _case_insensitive_value("robots")})
    canonical_tag = soup.find("link", attrs={"rel": _has_rel("canonical")})

    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()

    return {
        "title": _clean_text(title_tag.get_text(" ")) if title_tag else None,
        "meta_description": _content(description_tag),
        "canonical": _resolved_url(_attr(canonical_tag, "href"), page_url),
        "robots": _content(robots_tag),
        "links": _extract_links(soup, page_url),
        "text_length": len(_clean_text(soup.get_text(" "))),
        "script_count": len(BeautifulSoup(html, "html.parser").find_all("script")),
    }


def _case_insensitive_value(expected: str):
    return lambda value: isinstance(value, str) and value.lower() == expected


def _has_rel(expected: str):
    def matches(value) -> bool:
        if isinstance(value, list):
            return expected in [str(item).lower() for item in value]
        return isinstance(value, str) and expected in value.lower().split()

    return matches


def _content(tag) -> str | None:
    value = _attr(tag, "content")
    return _clean_text(value) if value else None


def _attr(tag, name: str) -> str | None:
    if tag is None or not tag.has_attr(name):
        return None
    value = str(tag.get(name) or "").strip()
    return value or None


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _resolved_url(raw_url: str | None, page_url: str) -> str | None:
    if not raw_url:
        return None
    try:
        return normalize_url(resolve_url(raw_url, page_url)).normalized_url
    except ValueError:
        return raw_url


def _extract_links(soup: BeautifulSoup, page_url: str) -> list[str]:
    links: set[str] = set()
    for tag in soup.find_all("a"):
        href = _attr(tag, "href")
        if not href or href.startswith("#"):
            continue
        if href.lower().startswith(("mailto:", "tel:", "javascript:")):
            continue
        resolved = _resolved_url(href, page_url)
        if resolved:
            links.add(resolved)
    return sorted(links)
