import json

from geo_seo_engine.crawler import CrawlPage, CrawlResult, DiscoveredLink, MainContent
from geo_seo_engine.internal_links import InternalLinkGraphOptions, run_internal_link_graph_audit


def test_connected_graph_builds_page_and_edge_metrics():
    result = run_internal_link_graph_audit(
        _crawl_result(),
        options=InternalLinkGraphOptions(hub_outbound_threshold=3),
    )

    home = _page(result, "https://example.com/")
    docs = _page(result, "https://example.com/docs")

    assert result.summary.total_pages == 6
    assert result.summary.internal_edges == 6
    assert result.summary.discovered_not_crawled_count == 1
    assert result.summary.extracted_content_pages == 1
    assert home.is_hub is True
    assert docs.inbound_internal_links == 1
    assert docs.outbound_internal_links == 1
    assert docs.inbound_anchor_texts == ["Docs"]


def test_detects_orphan_near_orphan_leaf_and_depth_signals():
    result = run_internal_link_graph_audit(_crawl_result(), options=InternalLinkGraphOptions(overly_deep_threshold=2))
    finding_ids = _finding_ids(result)

    assert "internal_links.orphan_page" in finding_ids
    assert "internal_links.near_orphan_page" in finding_ids
    assert "internal_links.weakly_connected_page" in finding_ids
    assert "internal_links.overly_deep_page" in finding_ids
    assert _page(result, "https://example.com/orphan").is_orphan is True
    assert _page(result, "https://example.com/deep").is_near_orphan is True
    assert result.summary.orphan_pages == 1
    assert result.summary.near_orphan_pages >= 1
    assert result.summary.leaf_pages >= 1
    assert result.summary.overly_deep_pages == 1


def test_detects_generic_repeated_and_weak_anchor_coverage():
    result = run_internal_link_graph_audit(_crawl_result())
    finding_ids = _finding_ids(result)

    assert "internal_links.generic_anchor_text" in finding_ids
    assert "internal_links.repeated_anchor_multiple_targets" in finding_ids
    assert "internal_links.weak_anchor_coverage" in finding_ids
    assert result.summary.generic_anchor_count == 2
    assert result.summary.missing_anchor_count == 1
    assert result.summary.repeated_anchor_texts == {"read more": 2}


def test_repeated_descriptive_anchor_is_low_diversity_not_anchor_coverage_gap():
    crawl_result = CrawlResult(
        start_url="https://example.com/",
        pages=[
            _crawl_page("https://example.com/", depth=0),
            _crawl_page("https://example.com/docs", depth=1, discovered_from="https://example.com/"),
            _crawl_page("https://example.com/services", depth=1, discovered_from="https://example.com/"),
        ],
        discovered_urls=[
            _link("https://example.com/", "https://example.com/docs", "Docs", depth=1),
            _link("https://example.com/", "https://example.com/services", "Services", depth=1),
            _link("https://example.com/docs", "https://example.com/services", "Services", depth=2),
        ],
    )

    result = run_internal_link_graph_audit(crawl_result)
    service_finding_ids = [
        finding.id
        for finding in result.findings
        if finding.page_url == "https://example.com/services"
    ]

    assert "internal_links.weak_anchor_coverage" not in service_finding_ids
    assert "internal_links.low_anchor_diversity" in service_finding_ids


def test_output_is_json_serializable():
    result = run_internal_link_graph_audit(_crawl_result())

    rendered = json.dumps(result.model_dump(mode="json"), sort_keys=True)

    assert "internal_links.orphan_page" in rendered
    assert "internal_edges" in rendered


def _crawl_result():
    return CrawlResult(
        start_url="https://example.com/",
        pages=[
            CrawlPage(
                url="https://example.com/",
                normalized_url="https://example.com/",
                final_url="https://example.com/",
                status_code=200,
                depth=0,
                links_found=5,
                main_content=MainContent(text="Home", text_length=4, word_count=1),
            ),
            _crawl_page("https://example.com/docs", depth=1, discovered_from="https://example.com/"),
            _crawl_page("https://example.com/pricing", depth=1, discovered_from="https://example.com/"),
            _crawl_page("https://example.com/blog", depth=2, discovered_from="https://example.com/docs"),
            _crawl_page("https://example.com/deep", depth=4, discovered_from="https://example.com/blog"),
            _crawl_page("https://example.com/orphan", depth=0),
        ],
        discovered_urls=[
            _link("https://example.com/", "https://example.com/docs", "Docs", depth=1),
            _link("https://example.com/", "https://example.com/pricing", "Read more", depth=1),
            _link("https://example.com/", "https://example.com/missing", "Missing", depth=1),
            _link("https://example.com/docs", "https://example.com/blog", "Blog", depth=2),
            _link("https://example.com/pricing", "https://example.com/blog", None, depth=2),
            _link("https://example.com/blog", "https://example.com/deep", "Read more", depth=3),
        ],
    )


def _crawl_page(url: str, depth: int, discovered_from: str | None = None):
    return CrawlPage(
        url=url,
        normalized_url=url,
        final_url=url,
        status_code=200,
        depth=depth,
        discovered_from=discovered_from,
        links_found=0,
    )


def _link(source: str, target: str, anchor_text: str | None, depth: int):
    return DiscoveredLink(
        raw_href=target,
        resolved_url=target,
        normalized_url=target,
        anchor_text=anchor_text,
        source_url=source,
        depth=depth,
    )


def _page(result, url: str):
    return next(page for page in result.pages if page.normalized_url == url)


def _finding_ids(result):
    return [finding.id for finding in result.findings]
