from __future__ import annotations

from collections import Counter

from geo_seo_engine.crawler.models import CrawlResult
from geo_seo_engine.inventory.models import (
    InventoryResult,
    InventorySkippedUrl,
    InventorySummary,
    InventoryUrl,
)


def build_url_inventory(crawl_result: CrawlResult) -> InventoryResult:
    urls: list[InventoryUrl] = []
    status_code_counts: Counter[str] = Counter()
    content_type_counts: Counter[str] = Counter()

    for page in crawl_result.pages:
        is_html = _is_html(page.content_type)
        is_success = 200 <= page.status_code <= 399 and page.error is None
        is_redirected = page.final_url != page.normalized_url
        has_error = page.error is not None or page.status_code == 0

        urls.append(
            InventoryUrl(
                url=page.url,
                normalized_url=page.normalized_url,
                final_url=page.final_url,
                status_code=page.status_code,
                depth=page.depth,
                content_type=page.content_type,
                is_html=is_html,
                is_success=is_success,
                is_redirected=is_redirected,
                has_error=has_error,
                error=page.error,
                discovered_from=page.discovered_from,
                links_found=page.links_found,
            )
        )
        status_code_counts[str(page.status_code)] += 1
        content_type_counts[page.content_type or "unknown"] += 1

    summary = InventorySummary(
        total_pages=len(urls),
        html_pages=sum(1 for url in urls if url.is_html),
        non_html_pages=sum(1 for url in urls if not url.is_html),
        success_pages=sum(1 for url in urls if url.is_success),
        redirected_pages=sum(1 for url in urls if url.is_redirected),
        error_pages=sum(1 for url in urls if url.has_error),
        skipped_urls=len(crawl_result.skipped_urls),
        max_depth=max((url.depth for url in urls), default=0),
        max_pages_reached=crawl_result.max_pages_reached,
        status_code_counts=dict(sorted(status_code_counts.items())),
        content_type_counts=dict(sorted(content_type_counts.items())),
    )

    return InventoryResult(
        start_url=crawl_result.start_url,
        urls=urls,
        skipped_urls=[
            InventorySkippedUrl(
                url=skipped.url,
                reason=skipped.reason,
                source_url=skipped.source_url,
            )
            for skipped in crawl_result.skipped_urls
        ],
        errors=list(crawl_result.errors),
        summary=summary,
    )


def _is_html(content_type: str | None) -> bool:
    return "text/html" in (content_type or "").lower()
