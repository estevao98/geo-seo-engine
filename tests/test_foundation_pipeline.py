import httpx

from geo_seo_engine.crawler import CrawlOptions, crawl_site
from geo_seo_engine.http import HttpClient
from geo_seo_engine.inventory import build_url_inventory
from geo_seo_engine.technical import TechnicalAuditOptions, run_technical_audit


def test_foundation_pipeline_crawls_inventory_and_audits_with_fake_http():
    requested_urls: list[str] = []
    responses = {
        "https://example.com/": (
            200,
            "text/html; charset=utf-8",
            """
            <html>
              <body>
                <a href="/docs">Docs</a>
                <a href="/broken">Broken page</a>
                <a href="https://other.example/external">External</a>
              </body>
            </html>
            """,
        ),
        "https://example.com/docs": (
            200,
            "text/html; charset=utf-8",
            "<html><body><h1>Docs</h1></body></html>",
        ),
        "https://example.com/broken": (
            404,
            "text/html; charset=utf-8",
            "<html><body><h1>Not found</h1></body></html>",
        ),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        status_code, content_type, html = responses[str(request.url)]
        return httpx.Response(
            status_code,
            headers={"content-type": content_type},
            text=html,
            request=request,
        )

    client = HttpClient(transport=httpx.MockTransport(handler))

    crawl_result = crawl_site(
        "https://example.com",
        options=CrawlOptions(max_pages=10, max_depth=2),
        http_client=client,
    )
    inventory = build_url_inventory(crawl_result)
    audit = run_technical_audit(
        inventory,
        options=TechnicalAuditOptions(max_depth_warning=2),
    )

    assert requested_urls == [
        "https://example.com/",
        "https://example.com/docs",
        "https://example.com/broken",
    ]
    assert crawl_result.start_url == "https://example.com/"
    assert len(crawl_result.pages) == 3
    assert [page.status_code for page in crawl_result.pages] == [200, 200, 404]
    assert crawl_result.discovered_urls[0].normalized_url == "https://example.com/docs"
    assert any(skip.reason == "external_host" for skip in crawl_result.skipped_urls)

    assert inventory.summary.total_pages == 3
    assert inventory.summary.html_pages == 3
    assert inventory.summary.success_pages == 2
    assert inventory.summary.error_pages == 0
    assert inventory.summary.skipped_urls == 1
    assert inventory.summary.status_code_counts == {"200": 2, "404": 1}
    assert inventory.urls[2].url == "https://example.com/broken"
    assert inventory.urls[2].is_success is False

    finding_ids = [finding.id for finding in audit.findings]
    assert "technical.status_not_200" in finding_ids
    assert "technical.zero_links_found" in finding_ids
    assert audit.summary.total_findings == len(audit.findings)
    assert audit.summary.by_severity["high"] == 1
    assert audit.summary.by_category["crawlability"] == len(audit.findings)
