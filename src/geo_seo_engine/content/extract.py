from __future__ import annotations

import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from geo_seo_engine.content.models import (
    ContentExtractionResult,
    ContentExtractionSummary,
    ContentHeading,
    ContentLink,
    ContentTextBlock,
    ExtractedMainContent,
)
from geo_seo_engine.core import is_same_site, normalize_url, resolve_url, url_host

_BOILERPLATE_SELECTORS = (
    "script, style, noscript, svg, template, nav, header, footer, aside, "
    "form, dialog, [hidden], [aria-hidden='true']"
)
_ARTICLE_SELECTORS = [
    "article",
    "[itemprop='articleBody']",
]
_TEXT_BLOCK_TAGS = {"p", "li", "blockquote", "pre"}
_BOILERPLATE_RE = re.compile(r"nav|menu|header|footer|sidebar|search|cookie|breadcrumb|promo|ad", re.I)
_CONTENT_RE = re.compile(r"article|main|content|post|entry|body|page", re.I)
_WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
_IGNORED_LINK_SCHEMES = {"mailto", "tel", "javascript", "data", "ftp"}


def extract_main_content_from_html(
    html: str,
    page_url: str,
    allowed_hosts: list[str] | None = None,
) -> ExtractedMainContent:
    soup = BeautifulSoup(html or "", "html.parser")
    metadata = _extract_metadata(soup, page_url)
    boilerplate_removed = _remove_non_content_nodes(soup)

    main_tag, method, confidence = _select_main_container(soup)
    if main_tag is None:
        plain_text = ""
        selector = None
        method = "empty_html"
        confidence = 0.0
    else:
        selector = _selector_for(main_tag)
        plain_text = _clean_text(main_tag.get_text(" "))
        if not plain_text:
            method = "empty_main_content"
            confidence = 0.0

    headings = _extract_headings(main_tag) if main_tag is not None else []
    text_blocks = _extract_text_blocks(main_tag) if main_tag is not None else []
    effective_allowed_hosts = allowed_hosts or _default_allowed_hosts(page_url)
    links = _extract_links(main_tag, page_url, effective_allowed_hosts) if main_tag is not None else []
    image_alt_texts = _extract_image_alt_texts(main_tag) if main_tag is not None else []
    internal_link_count = sum(1 for link in links if link.is_internal)
    word_count = _word_count(plain_text)

    return ExtractedMainContent(
        page_url=page_url,
        title=metadata["title"],
        meta_description=metadata["meta_description"],
        canonical_url=metadata["canonical_url"],
        extraction_method=method,
        main_selector=selector,
        confidence=confidence,
        headings=headings,
        text_blocks=text_blocks,
        links=links,
        image_alt_texts=image_alt_texts,
        plain_text=plain_text,
        word_count=word_count,
        character_count=len(plain_text),
        paragraph_count=sum(1 for block in text_blocks if block.tag == "p"),
        heading_count=len(headings),
        link_count=len(links),
        internal_link_count=internal_link_count,
        external_link_count=len(links) - internal_link_count,
        boilerplate_removed=boilerplate_removed,
    )


def summarize_content_extraction(
    pages: list[ExtractedMainContent],
    start_url: str | None = None,
) -> ContentExtractionResult:
    total_pages = len(pages)
    pages_with_main_content = sum(1 for page in pages if page.word_count > 0)
    extraction_methods: dict[str, int] = {}
    for page in pages:
        extraction_methods[page.extraction_method] = extraction_methods.get(page.extraction_method, 0) + 1

    summary = ContentExtractionSummary(
        total_pages=total_pages,
        pages_with_main_content=pages_with_main_content,
        pages_missing_main_content=total_pages - pages_with_main_content,
        average_word_count=(sum(page.word_count for page in pages) / total_pages) if total_pages else 0.0,
        low_word_count_pages=[page.page_url for page in pages if page.word_count < 50],
        extraction_methods=extraction_methods,
    )
    return ContentExtractionResult(start_url=start_url, pages=pages, summary=summary)


def _extract_metadata(soup: BeautifulSoup, page_url: str) -> dict[str, str | None]:
    title = _clean_text(soup.title.get_text(" ")) if soup.title else None
    description_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in _rel_values(value))
    canonical_url = None
    if canonical_tag and canonical_tag.get("href"):
        try:
            canonical_url = normalize_url(resolve_url(str(canonical_tag["href"]), page_url)).normalized_url
        except ValueError:
            canonical_url = str(canonical_tag["href"]).strip() or None

    return {
        "title": title or None,
        "meta_description": _string_attribute(description_tag.get("content")) if description_tag else None,
        "canonical_url": canonical_url,
    }


def _remove_non_content_nodes(soup: BeautifulSoup) -> bool:
    removed = False
    for tag in soup.select(_BOILERPLATE_SELECTORS):
        tag.decompose()
        removed = True
    for tag in soup.find_all(True):
        if _is_boilerplate_tag(tag):
            tag.decompose()
            removed = True
    return removed


def _select_main_container(soup: BeautifulSoup):
    for selector, method, confidence in [
        ("main", "main_element", 0.95),
        ("[role='main']", "role_main", 0.9),
    ]:
        for tag in soup.select(selector):
            if _has_content(tag):
                return tag, method, confidence

    for selector in _ARTICLE_SELECTORS:
        candidate = _best_by_text_length(soup.select(selector))
        if candidate is not None:
            return candidate, "article_like", 0.8

    candidates = [tag for tag in soup.find_all(["article", "section", "div", "body"]) if _has_content(tag)]
    if candidates:
        scored = [(_candidate_score(tag), tag) for tag in candidates]
        score, tag = max(scored, key=lambda item: item[0])
        return tag, "scored_candidate", max(0.35, min(0.75, score / 1200))

    fallback = soup.body or soup
    if _has_content(fallback):
        return fallback, "body_fallback", 0.3
    return None, "empty_html", 0.0


def _candidate_score(tag) -> float:
    text = _clean_text(tag.get_text(" "))
    words = _word_count(text)
    paragraphs = len(tag.find_all("p"))
    headings = len(tag.find_all(re.compile(r"^h[1-3]$")))
    links = tag.find_all("a")
    link_text_words = sum(_word_count(link.get_text(" ")) for link in links)
    link_density = link_text_words / words if words else 1.0
    score = len(text) + paragraphs * 80 + headings * 45
    score -= score * min(link_density, 1.0) * 0.55
    if _is_boilerplate_tag(tag):
        score -= 300
    if _content_identity(tag):
        score += 180
    return score


def _extract_headings(tag) -> list[ContentHeading]:
    headings: list[ContentHeading] = []
    for heading in tag.find_all(re.compile(r"^h[1-3]$")):
        text = _clean_text(heading.get_text(" "))
        if text:
            headings.append(ContentHeading(level=int(heading.name[1]), text=text, order=len(headings)))
    return headings


def _extract_text_blocks(tag) -> list[ContentTextBlock]:
    blocks: list[ContentTextBlock] = []
    for block in tag.find_all(_TEXT_BLOCK_TAGS):
        text = _clean_text(block.get_text(" "))
        if text:
            blocks.append(
                ContentTextBlock(text=text, tag=block.name, word_count=_word_count(text), order=len(blocks))
            )
    if not blocks:
        text = _clean_text(tag.get_text(" "))
        if text:
            blocks.append(ContentTextBlock(text=text, tag=tag.name or "document", word_count=_word_count(text), order=0))
    return blocks


def _extract_links(tag, page_url: str, allowed_hosts: list[str]) -> list[ContentLink]:
    links: list[ContentLink] = []
    for anchor in tag.find_all("a"):
        raw_href = str(anchor.get("href") or "").strip()
        if not raw_href or raw_href.startswith("#"):
            continue
        if urlsplit(raw_href).scheme.lower() in _IGNORED_LINK_SCHEMES:
            continue
        try:
            normalized_url = normalize_url(resolve_url(raw_href, page_url)).normalized_url
        except ValueError:
            continue
        links.append(
            ContentLink(
                url=normalized_url,
                anchor_text=_clean_text(anchor.get_text(" ")) or None,
                is_internal=is_same_site(normalized_url, allowed_hosts),
            )
        )
    return links


def _extract_image_alt_texts(tag) -> list[str]:
    alt_texts: list[str] = []
    for image in tag.find_all("img"):
        if image.has_attr("alt"):
            alt = _clean_text(str(image.get("alt") or ""))
            if alt:
                alt_texts.append(alt)
    return alt_texts


def _best_by_text_length(tags):
    candidates = [tag for tag in tags if _has_content(tag)]
    if not candidates:
        return None
    return max(candidates, key=lambda tag: len(_clean_text(tag.get_text(" "))))


def _has_content(tag) -> bool:
    return bool(_clean_text(tag.get_text(" ")))


def _is_boilerplate_tag(tag) -> bool:
    return _matches_identity(tag, _BOILERPLATE_RE) or str(tag.get("role") or "").lower() in {
        "navigation",
        "banner",
        "contentinfo",
        "search",
        "complementary",
    }


def _content_identity(tag) -> bool:
    return _matches_identity(tag, _CONTENT_RE)


def _matches_identity(tag, pattern: re.Pattern[str]) -> bool:
    values = [str(tag.get("id") or ""), " ".join(tag.get("class") or [])]
    return any(pattern.search(value) for value in values)


def _selector_for(tag) -> str | None:
    name = getattr(tag, "name", None)
    if not name or name == "[document]":
        return None
    if tag.get("id"):
        return f"{name}#{tag['id']}"
    classes = tag.get("class") or []
    if classes:
        return f"{name}.{classes[0]}"
    if tag.get("role"):
        return f"{name}[role='{tag['role']}']"
    return name


def _default_allowed_hosts(page_url: str) -> list[str]:
    host = url_host(page_url)
    return [host] if host else []


def _string_attribute(value) -> str | None:
    if value is None:
        return None
    cleaned = _clean_text(str(value))
    return cleaned or None


def _rel_values(value) -> set[str]:
    if isinstance(value, str):
        return {part.lower() for part in value.split()}
    return {str(part).lower() for part in value}


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))
