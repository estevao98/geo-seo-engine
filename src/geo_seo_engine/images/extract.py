from __future__ import annotations

from bs4 import BeautifulSoup

from geo_seo_engine.core import is_same_site, normalize_url, resolve_url, url_host
from geo_seo_engine.images.models import ImageResource, ImageSrcsetCandidate, PageImageInventory, SkippedImage


def extract_images_from_html(
    html: str,
    page_url: str,
    allowed_hosts: list[str] | None = None,
) -> PageImageInventory:
    images: list[ImageResource] = []
    skipped_images: list[SkippedImage] = []
    soup = BeautifulSoup(html, "html.parser")
    effective_allowed_hosts = allowed_hosts or _default_allowed_hosts(page_url)

    for tag in soup.find_all("img"):
        raw_src_value = tag.get("src")
        raw_src = str(raw_src_value).strip() if raw_src_value is not None else ""
        if not raw_src:
            skipped_images.append(
                SkippedImage(
                    page_url=page_url,
                    reason="missing_src",
                    raw_src=raw_src if raw_src_value is not None else None,
                )
            )
            continue

        is_data_uri = raw_src.lower().startswith("data:")
        if is_data_uri:
            resolved_src = raw_src
            normalized_src = raw_src
            is_external = False
        else:
            try:
                resolved_src = resolve_url(raw_src, page_url)
                normalized = normalize_url(resolved_src)
            except ValueError:
                skipped_images.append(
                    SkippedImage(
                        page_url=page_url,
                        reason="invalid_src",
                        raw_src=raw_src,
                    )
                )
                continue
            normalized_src = normalized.normalized_url
            is_external = not is_same_site(normalized_src, effective_allowed_hosts)

        images.append(
            ImageResource(
                page_url=page_url,
                raw_src=raw_src,
                resolved_src=resolved_src,
                normalized_src=normalized_src,
                alt=str(tag.get("alt")) if tag.has_attr("alt") else None,
                has_alt_attribute=tag.has_attr("alt"),
                width=_string_attribute(tag.get("width")),
                height=_string_attribute(tag.get("height")),
                loading=_string_attribute(tag.get("loading")),
                srcset=_string_attribute(tag.get("srcset")),
                srcset_candidates=_parse_srcset(_string_attribute(tag.get("srcset"))),
                is_decorative=_is_decorative(tag),
                is_data_uri=is_data_uri,
                is_external=is_external,
            )
        )

    return PageImageInventory(
        page_url=page_url,
        images=images,
        skipped_images=skipped_images,
    )


def _default_allowed_hosts(page_url: str) -> list[str]:
    host = url_host(page_url)
    return [host] if host else []


def _string_attribute(value) -> str | None:
    if value is None:
        return None
    return str(value)


def _is_decorative(tag) -> bool:
    role = _string_attribute(tag.get("role"))
    aria_hidden = _string_attribute(tag.get("aria-hidden"))
    return (role or "").strip().lower() in {"presentation", "none"} or (
        aria_hidden or ""
    ).strip().lower() == "true"


def _parse_srcset(value: str | None) -> list[ImageSrcsetCandidate]:
    if not value:
        return []

    candidates: list[ImageSrcsetCandidate] = []
    index = 0
    length = len(value)

    while index < length:
        while index < length and (value[index].isspace() or value[index] == ","):
            index += 1
        if index >= length:
            break

        url_start = index
        if value[index:].lower().startswith("data:"):
            while index < length and not value[index].isspace():
                index += 1
        else:
            while index < length and not value[index].isspace() and value[index] != ",":
                index += 1

        raw_url = value[url_start:index].strip()
        while index < length and value[index].isspace():
            index += 1

        descriptor_start = index
        while index < length and value[index] != ",":
            index += 1
        descriptor = value[descriptor_start:index].strip() or None

        if raw_url:
            candidates.append(ImageSrcsetCandidate(raw_url=raw_url, descriptor=descriptor))

        if index < length and value[index] == ",":
            index += 1

    return candidates
