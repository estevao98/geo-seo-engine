import json

from geo_seo_engine.inventory import (
    InventoryResult,
    InventorySkippedUrl,
    InventorySummary,
    InventoryUrl,
)
from geo_seo_engine.technical import TechnicalAuditOptions, run_technical_audit


def _inventory(
    urls: list[InventoryUrl],
    *,
    skipped_urls: int = 0,
    skipped_reasons: list[str] | None = None,
    max_pages_reached: bool = False,
) -> InventoryResult:
    skipped_url_items = [
        InventorySkippedUrl(
            url=f"https://example.com/skipped-{index}",
            reason=reason,
            source_url="https://example.com/",
        )
        for index, reason in enumerate(skipped_reasons or [], start=1)
    ]
    return InventoryResult(
        start_url="https://example.com/",
        urls=urls,
        skipped_urls=skipped_url_items,
        summary=InventorySummary(
            total_pages=len(urls),
            html_pages=sum(1 for url in urls if url.is_html),
            non_html_pages=sum(1 for url in urls if not url.is_html),
            success_pages=sum(1 for url in urls if url.is_success),
            redirected_pages=sum(1 for url in urls if url.is_redirected),
            error_pages=sum(1 for url in urls if url.has_error),
            skipped_urls=skipped_urls,
            max_depth=max((url.depth for url in urls), default=0),
            max_pages_reached=max_pages_reached,
        ),
    )


def _url(**overrides) -> InventoryUrl:
    defaults = {
        "url": "https://example.com/",
        "normalized_url": "https://example.com/",
        "final_url": "https://example.com/",
        "status_code": 200,
        "depth": 0,
        "content_type": "text/html",
        "is_html": True,
        "is_success": True,
        "is_redirected": False,
        "has_error": False,
        "error": None,
        "links_found": 1,
    }
    defaults.update(overrides)
    return InventoryUrl(**defaults)


def _finding_ids(result) -> list[str]:
    return [finding.id for finding in result.findings]


def test_technical_audit_finds_status_not_200():
    result = run_technical_audit(_inventory([_url(status_code=404, is_success=False)]))

    assert "technical.status_not_200" in _finding_ids(result)
    finding = result.findings[0]
    assert finding.severity == "high"
    assert finding.evidence[0].observed == 404


def test_technical_audit_finds_fetch_error():
    result = run_technical_audit(
        _inventory(
            [
                _url(
                    status_code=0,
                    is_success=False,
                    content_type=None,
                    is_html=False,
                    is_redirected=True,
                    has_error=True,
                    error="request_error: timeout",
                    links_found=0,
                )
            ]
        )
    )

    assert _finding_ids(result) == ["technical.fetch_error"]
    assert any(
        "timeout" in str(finding.evidence[0].observed)
        for finding in result.findings
    )


def test_technical_audit_finds_non_html_url():
    result = run_technical_audit(
        _inventory(
            [
                _url(
                    url="https://example.com/file.pdf",
                    normalized_url="https://example.com/file.pdf",
                    final_url="https://example.com/file.pdf",
                    content_type="application/pdf",
                    is_html=False,
                )
            ]
        )
    )

    assert "technical.non_html_url" in _finding_ids(result)
    assert result.findings[0].severity == "info"


def test_technical_audit_does_not_find_non_html_url_when_fetch_failed():
    result = run_technical_audit(
        _inventory(
            [
                _url(
                    url="https://example.com/file.pdf",
                    normalized_url="https://example.com/file.pdf",
                    final_url="https://example.com/file.pdf",
                    status_code=0,
                    content_type=None,
                    is_html=False,
                    is_success=False,
                    has_error=True,
                    error="request_error: timeout",
                )
            ]
        )
    )

    assert "technical.non_html_url" not in _finding_ids(result)


def test_technical_audit_respects_flag_non_html_false():
    result = run_technical_audit(
        _inventory(
            [
                _url(
                    url="https://example.com/file.pdf",
                    normalized_url="https://example.com/file.pdf",
                    final_url="https://example.com/file.pdf",
                    content_type="application/pdf",
                    is_html=False,
                )
            ]
        ),
        options=TechnicalAuditOptions(flag_non_html=False),
    )

    assert "technical.non_html_url" not in _finding_ids(result)


def test_technical_audit_finds_redirect():
    result = run_technical_audit(
        _inventory(
            [
                _url(
                    url="https://example.com/old",
                    normalized_url="https://example.com/old",
                    final_url="https://example.com/new",
                    status_code=301,
                    is_redirected=True,
                )
            ]
        )
    )

    assert "technical.redirected_url" in _finding_ids(result)
    assert "technical.status_not_200" not in _finding_ids(result)


def test_technical_audit_respects_flag_redirects_false():
    result = run_technical_audit(
        _inventory(
            [
                _url(
                    url="https://example.com/old",
                    normalized_url="https://example.com/old",
                    final_url="https://example.com/new",
                    status_code=301,
                    is_redirected=True,
                )
            ]
        ),
        options=TechnicalAuditOptions(flag_redirects=False),
    )

    assert "technical.redirected_url" not in _finding_ids(result)
    assert "technical.status_not_200" not in _finding_ids(result)


def test_technical_audit_finds_deep_page():
    result = run_technical_audit(
        _inventory([_url(depth=4)]),
        options=TechnicalAuditOptions(max_depth_warning=3),
    )

    assert "technical.deep_page" in _finding_ids(result)


def test_technical_audit_does_not_warn_when_depth_equals_threshold():
    result = run_technical_audit(
        _inventory([_url(depth=3)]),
        options=TechnicalAuditOptions(max_depth_warning=3),
    )

    assert "technical.deep_page" not in _finding_ids(result)


def test_technical_audit_finds_html_page_with_zero_links():
    result = run_technical_audit(_inventory([_url(links_found=0)]))

    assert "technical.zero_links_found" in _finding_ids(result)
    assert result.findings[0].severity == "low"


def test_technical_audit_respects_flag_zero_links_false():
    result = run_technical_audit(
        _inventory([_url(links_found=0)]),
        options=TechnicalAuditOptions(flag_zero_links=False),
    )

    assert "technical.zero_links_found" not in _finding_ids(result)


def test_technical_audit_does_not_warn_zero_links_for_non_200_or_non_html():
    result = run_technical_audit(
        _inventory(
            [
                _url(status_code=404, is_success=False, links_found=0),
                _url(
                    url="https://example.com/file.pdf",
                    normalized_url="https://example.com/file.pdf",
                    final_url="https://example.com/file.pdf",
                    content_type="application/pdf",
                    is_html=False,
                    links_found=0,
                ),
            ]
        )
    )

    assert "technical.zero_links_found" not in _finding_ids(result)


def test_technical_audit_finds_max_pages_reached():
    result = run_technical_audit(_inventory([_url()], max_pages_reached=True))

    assert "technical.max_pages_reached" in _finding_ids(result)


def test_technical_audit_finds_high_skipped_urls():
    result = run_technical_audit(
        _inventory(
            [_url()],
            skipped_urls=26,
            skipped_reasons=["external_host", "external_host", "excluded_by_pattern"],
        ),
        options=TechnicalAuditOptions(high_skipped_urls_warning=25),
    )

    assert "technical.high_skipped_urls" in _finding_ids(result)
    assert result.findings[0].evidence[0].observed == 26
    assert result.findings[0].evidence[1].observed == (
        "excluded_by_pattern=1, external_host=2"
    )


def test_technical_audit_does_not_warn_when_skipped_urls_equals_threshold():
    result = run_technical_audit(
        _inventory([_url()], skipped_urls=25),
        options=TechnicalAuditOptions(high_skipped_urls_warning=25),
    )

    assert "technical.high_skipped_urls" not in _finding_ids(result)


def test_technical_audit_finds_duplicate_final_url():
    result = run_technical_audit(
        _inventory(
            [
                _url(url="https://example.com/a", normalized_url="https://example.com/a"),
                _url(url="https://example.com/b", normalized_url="https://example.com/b"),
            ]
        )
    )

    assert "technical.duplicate_final_url" in _finding_ids(result)


def test_technical_audit_ignores_duplicate_final_url_for_same_normalized_url():
    result = run_technical_audit(
        _inventory(
            [
                _url(url="https://example.com/a", normalized_url="https://example.com/a"),
                _url(
                    url="https://example.com/a#fragment",
                    normalized_url="https://example.com/a",
                ),
            ]
        )
    )

    assert "technical.duplicate_final_url" not in _finding_ids(result)


def test_technical_audit_summary_by_severity():
    result = run_technical_audit(
        _inventory(
            [
                _url(status_code=404, is_success=False),
                _url(
                    url="https://example.com/file.pdf",
                    normalized_url="https://example.com/file.pdf",
                    final_url="https://example.com/file.pdf",
                    content_type="application/pdf",
                    is_html=False,
                ),
            ]
        )
    )

    assert result.summary.by_severity["high"] == 1
    assert result.summary.by_severity["info"] == 1


def test_technical_audit_summary_by_category():
    result = run_technical_audit(
        _inventory(
            [
                _url(status_code=404, is_success=False),
                _url(
                    url="https://example.com/file.pdf",
                    normalized_url="https://example.com/file.pdf",
                    final_url="https://example.com/file.pdf",
                    content_type="application/pdf",
                    is_html=False,
                ),
            ]
        )
    )

    assert result.summary.by_category["crawlability"] == 1
    assert result.summary.by_category["technical"] == 1


def test_technical_audit_output_is_json_serializable():
    result = run_technical_audit(_inventory([_url(links_found=0)]))

    rendered = json.dumps(result.model_dump(mode="json"))

    assert json.loads(rendered)["summary"]["total_findings"] == 1
