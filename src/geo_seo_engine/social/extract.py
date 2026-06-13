from __future__ import annotations

from collections import Counter
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from geo_seo_engine.core import is_same_site, normalize_url, resolve_url, url_host
from geo_seo_engine.social.models import PageSocialMetadata, SocialImageReference, SocialMetaTag

SOCIAL_IMAGE_KEYS = {"og:image", "twitter:image"}
SUPPORTED_SOCIAL_IMAGE_SCHEMES = {"http", "https"}


def extract_social_metadata_from_html(
    html: str,
    page_url: str,
    allowed_hosts: list[str] | None = None,
) -> PageSocialMetadata:
    tags: list[SocialMetaTag] = []
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all("meta"):
        attribute_name = "property" if tag.has_attr("property") else "name" if tag.has_attr("name") else None
        if attribute_name is None:
            continue

        raw_key = str(tag.get(attribute_name) or "").strip()
        key = raw_key.lower()
        kind = _social_kind(key)
        if kind == "other":
            continue

        content = str(tag.get("content") or "").strip()
        tags.append(
            SocialMetaTag(
                page_url=page_url,
                kind=kind,
                key=key,
                raw_key=raw_key,
                content=content,
                attribute_name=attribute_name,
                is_empty=content == "",
            )
        )

    open_graph = _metadata_dict(tags, "og")
    twitter = _metadata_dict(tags, "twitter")
    duplicates = {key: count for key, count in Counter(tag.key for tag in tags).items() if count > 1}
    effective_allowed_hosts = allowed_hosts or _default_allowed_hosts(page_url)

    return PageSocialMetadata(
        page_url=page_url,
        tags=tags,
        open_graph=open_graph,
        twitter=twitter,
        duplicates=dict(sorted(duplicates.items())),
        image_references=[
            _build_image_reference(tag, page_url, effective_allowed_hosts)
            for tag in tags
            if tag.key in SOCIAL_IMAGE_KEYS and not tag.is_empty
        ],
    )


def _metadata_dict(tags: list[SocialMetaTag], kind: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for tag in tags:
        if tag.kind != kind:
            continue
        if tag.key not in values or (not values[tag.key] and tag.content):
            values[tag.key] = tag.content
    return values


def _social_kind(key: str):
    if key.startswith("og:"):
        return "og"
    if key.startswith("twitter:"):
        return "twitter"
    return "other"


def _build_image_reference(
    tag: SocialMetaTag,
    page_url: str,
    allowed_hosts: list[str],
) -> SocialImageReference:
    raw_url = tag.content
    if raw_url.lower().startswith("data:"):
        return SocialImageReference(
            page_url=page_url,
            metadata_key=tag.key,
            raw_url=raw_url,
            is_invalid=True,
            is_data_uri=True,
        )

    has_whitespace = any(character.isspace() for character in raw_url)

    try:
        parsed = urlsplit(raw_url)
    except ValueError:
        return SocialImageReference(
            page_url=page_url,
            metadata_key=tag.key,
            raw_url=raw_url,
            is_invalid=True,
        )
    is_relative = not parsed.scheme and not parsed.netloc
    if has_whitespace or (parsed.scheme and parsed.scheme.lower() not in SUPPORTED_SOCIAL_IMAGE_SCHEMES):
        return SocialImageReference(
            page_url=page_url,
            metadata_key=tag.key,
            raw_url=raw_url,
            is_relative=is_relative,
            is_invalid=True,
        )

    try:
        resolved_url = resolve_url(raw_url, page_url)
        normalized_url = normalize_url(resolved_url).normalized_url
    except ValueError:
        return SocialImageReference(
            page_url=page_url,
            metadata_key=tag.key,
            raw_url=raw_url,
            is_relative=is_relative,
            is_invalid=True,
        )

    return SocialImageReference(
        page_url=page_url,
        metadata_key=tag.key,
        raw_url=raw_url,
        resolved_url=resolved_url,
        normalized_url=normalized_url,
        is_relative=is_relative,
        is_external=not is_same_site(normalized_url, allowed_hosts),
    )


def _default_allowed_hosts(page_url: str) -> list[str]:
    host = url_host(page_url)
    return [host] if host else []
