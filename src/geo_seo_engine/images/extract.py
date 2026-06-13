from __future__ import annotations

from bs4 import BeautifulSoup

from geo_seo_engine.core import is_same_site, normalize_url, resolve_url, url_host
from geo_seo_engine.images.models import ImageResource, PageImageInventory, SkippedImage


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
