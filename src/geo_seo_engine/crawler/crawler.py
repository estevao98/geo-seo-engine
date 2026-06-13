from __future__ import annotations

from collections import deque
from collections.abc import Callable

from geo_seo_engine.core import is_same_site, normalize_url
from geo_seo_engine.crawler.extract import extract_links
from geo_seo_engine.crawler.models import CrawlOptions, CrawlPage, CrawlResult, SkippedUrl
from geo_seo_engine.http import HttpClient


def crawl_site(
    start_url: str,
    options: CrawlOptions | None = None,
    *,
    http_client: HttpClient | None = None,
    on_html_page: Callable[..., None] | None = None,
) -> CrawlResult:
    active_options = options or CrawlOptions()
    start_identity = normalize_url(start_url)
    allowed_hosts = active_options.allowed_hosts or [start_identity.host]
    client = http_client or HttpClient()

    result = CrawlResult(start_url=start_identity.normalized_url)

    if active_options.allowed_hosts and not is_same_site(start_identity.normalized_url, allowed_hosts):
        result.skipped_urls.append(
            SkippedUrl(
                url=start_identity.normalized_url,
                reason="start_url_outside_allowed_hosts",
            )
        )
        result.errors.append(f"{start_identity.normalized_url}: start_url_outside_allowed_hosts")
        return result

    frontier = deque([(start_identity.normalized_url, 0, None)])
    queued_or_fetched = {start_identity.normalized_url}
    discovered_urls: set[str] = set()

    while frontier and len(result.pages) < active_options.max_pages:
        url, depth, discovered_from = frontier.popleft()
        fetch_result = client.fetch(url)
        final_url = fetch_result.final_url or url
        requested_normalized_url = _normalize_or_original(url)

        final_url_in_scope = False

        try:
            page_identity = normalize_url(final_url)
            final_normalized_url = page_identity.normalized_url
            final_url_in_scope = is_same_site(final_normalized_url, allowed_hosts)
        except ValueError:
            final_normalized_url = final_url

        links_found = 0
        page_error = fetch_result.error

        if page_error:
            result.errors.append(f"{url}: {page_error}")
        elif not final_url_in_scope:
            result.skipped_urls.append(
                SkippedUrl(
                    url=final_url,
                    reason="final_url_outside_allowed_hosts",
                    source_url=url,
                )
            )
        elif fetch_result.ok and _is_html(fetch_result.content_type):
            if on_html_page:
                on_html_page(
                    page_url=url,
                    normalized_url=requested_normalized_url,
                    final_url=final_url,
                    html=fetch_result.text,
                    content_type=fetch_result.content_type,
                    depth=depth,
                )

            links, skipped = extract_links(
                fetch_result.text,
                final_url,
                allowed_hosts,
                source_depth=depth,
                include_patterns=active_options.include_patterns,
                exclude_patterns=active_options.exclude_patterns,
            )
            links_found = len(links)
            result.skipped_urls.extend(skipped)

            for link in links:
                if link.normalized_url not in discovered_urls:
                    result.discovered_urls.append(link)
                    discovered_urls.add(link.normalized_url)

                if link.depth > active_options.max_depth:
                    result.skipped_urls.append(
                        SkippedUrl(
                            url=link.normalized_url,
                            reason="max_depth_exceeded",
                            source_url=link.source_url,
                        )
                    )
                    continue

                if link.normalized_url in queued_or_fetched:
                    result.skipped_urls.append(
                        SkippedUrl(
                            url=link.normalized_url,
                            reason="duplicate_normalized_url",
                            source_url=link.source_url,
                        )
                    )
                    continue

                frontier.append((link.normalized_url, link.depth, requested_normalized_url))
                queued_or_fetched.add(link.normalized_url)

        result.pages.append(
            CrawlPage(
                url=url,
                normalized_url=requested_normalized_url,
                final_url=final_url,
                status_code=fetch_result.status_code,
                depth=depth,
                discovered_from=discovered_from,
                content_type=fetch_result.content_type or None,
                error=page_error,
                links_found=links_found,
            )
        )

    result.max_pages_reached = bool(frontier and len(result.pages) >= active_options.max_pages)
    return result


def _is_html(content_type: str | None) -> bool:
    return "text/html" in (content_type or "").lower()


def _normalize_or_original(url: str) -> str:
    try:
        return normalize_url(url).normalized_url
    except ValueError:
        return url
