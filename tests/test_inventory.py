import json

from geo_seo_engine.crawler import CrawlPage, CrawlResult, SkippedUrl
from geo_seo_engine.inventory import build_url_inventory


def test_inventory_with_html_200_page():
    result = build_url_inventory(
        CrawlResult(
            start_url="https://example.com/",
            pages=[
                CrawlPage(
                    url="https://example.com/",
                    normalized_url="https://example.com/",
                    final_url="https://example.com/",
                    status_code=200,
                    depth=0,
                    content_type="text/html; charset=utf-8",
                    links_found=3,
                )
            ],
        )
    )

    assert result.urls[0].is_html is True
    assert result.urls[0].is_success is True
    assert result.urls[0].is_redirected is False
    assert result.urls[0].has_error is False
    assert result.urls[0].links_found == 3
    assert result.summary.total_pages == 1
    assert result.summary.html_pages == 1
    assert result.summary.success_pages == 1


def test_inventory_with_non_html_page():
    result = build_url_inventory(
        CrawlResult(
            start_url="https://example.com/file.pdf",
            pages=[
                CrawlPage(
                    url="https://example.com/file.pdf",
                    normalized_url="https://example.com/file.pdf",
                    final_url="https://example.com/file.pdf",
                    status_code=200,
                    depth=0,
                    content_type="application/pdf",
                )
            ],
        )
    )

    assert result.urls[0].is_html is False
    assert result.summary.html_pages == 0
    assert result.summary.non_html_pages == 1


def test_inventory_with_redirected_page():
    result = build_url_inventory(
        CrawlResult(
            start_url="https://example.com/old",
            pages=[
                CrawlPage(
                    url="https://example.com/old",
                    normalized_url="https://example.com/old",
                    final_url="https://example.com/new",
                    status_code=301,
                    depth=0,
                    content_type="text/html",
                )
            ],
        )
    )

    assert result.urls[0].is_redirected is True
    assert result.urls[0].is_success is True
    assert result.summary.redirected_pages == 1


def test_inventory_with_error_page():
    result = build_url_inventory(
        CrawlResult(
            start_url="https://example.com/",
            pages=[
                CrawlPage(
                    url="https://example.com/",
                    normalized_url="https://example.com/",
                    final_url="https://example.com/",
                    status_code=0,
                    depth=0,
                    error="request_error: connection failed",
                )
            ],
        )
    )

    assert result.urls[0].has_error is True
    assert result.urls[0].is_success is False
    assert result.summary.error_pages == 1


def test_inventory_preserves_skipped_urls_and_errors():
    result = build_url_inventory(
        CrawlResult(
            start_url="https://example.com/",
            skipped_urls=[
                SkippedUrl(
                    url="https://other.example/",
                    reason="external_host",
                    source_url="https://example.com/",
                )
            ],
            errors=["https://example.com/: request_error: timeout"],
        )
    )

    assert result.skipped_urls[0].url == "https://other.example/"
    assert result.skipped_urls[0].reason == "external_host"
    assert result.skipped_urls[0].source_url == "https://example.com/"
    assert result.errors == ["https://example.com/: request_error: timeout"]
    assert result.summary.skipped_urls == 1


def test_inventory_calculates_summary_counts_depth_and_max_pages():
    result = build_url_inventory(
        CrawlResult(
            start_url="https://example.com/",
            pages=[
                CrawlPage(
                    url="https://example.com/",
                    normalized_url="https://example.com/",
                    final_url="https://example.com/",
                    status_code=200,
                    depth=0,
                    content_type="text/html; charset=utf-8",
                ),
                CrawlPage(
                    url="https://example.com/feed.xml",
                    normalized_url="https://example.com/feed.xml",
                    final_url="https://example.com/feed.xml",
                    status_code=404,
                    depth=2,
                    content_type="application/xml",
                ),
                CrawlPage(
                    url="https://example.com/missing-type",
                    normalized_url="https://example.com/missing-type",
                    final_url="https://example.com/missing-type",
                    status_code=200,
                    depth=1,
                    content_type=None,
                ),
            ],
            max_pages_reached=True,
        )
    )

    assert result.summary.status_code_counts == {"200": 2, "404": 1}
    assert result.summary.content_type_counts == {
        "application/xml": 1,
        "text/html; charset=utf-8": 1,
        "unknown": 1,
    }
    assert result.summary.max_depth == 2
    assert result.summary.max_pages_reached is True


def test_inventory_output_is_json_serializable():
    result = build_url_inventory(
        CrawlResult(
            start_url="https://example.com/",
            pages=[
                CrawlPage(
                    url="https://example.com/",
                    normalized_url="https://example.com/",
                    final_url="https://example.com/",
                    status_code=200,
                    depth=0,
                    content_type="text/html",
                )
            ],
        )
    )

    rendered = json.dumps(result.model_dump(mode="json"))

    assert json.loads(rendered)["summary"]["total_pages"] == 1
