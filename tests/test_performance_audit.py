from geo_seo_engine.core.models import IssueCategory, Severity
from geo_seo_engine.performance import (
    PagePerformanceSnapshot,
    PerformanceAuditOptions,
    PerformanceMetric,
    PerformanceOpportunity,
    run_performance_audit,
)
from geo_seo_engine.performance.client import PerformanceDataProvider


def test_run_performance_audit_flags_expected_performance_findings():
    page = PagePerformanceSnapshot(
        page_url="https://example.com/",
        performance_score=42,
        has_lab_data=True,
        has_field_data=False,
        metrics=[
            PerformanceMetric(id="largest-contentful-paint", label="LCP", value=4100, unit="ms", display_value="4.1 s"),
            PerformanceMetric(id="cumulative-layout-shift", label="CLS", value=0.31, unit="score", display_value="0.31"),
            PerformanceMetric(id="interaction-to-next-paint", label="INP", value=650, unit="ms", display_value="650 ms"),
            PerformanceMetric(id="total-blocking-time", label="TBT", value=620, unit="ms", display_value="620 ms"),
        ],
        opportunities=[
            PerformanceOpportunity(
                id="unused-javascript",
                title="Reduce unused JavaScript",
                estimated_savings_ms=1400,
                estimated_savings_bytes=640000,
            )
        ],
    )

    result = run_performance_audit([page], start_url="https://example.com/")
    finding_ids = [finding.id for finding in result.findings]

    assert "performance.low_score" in finding_ids
    assert "performance.lcp_slow" in finding_ids
    assert "performance.cls_poor" in finding_ids
    assert "performance.inp_slow" in finding_ids
    assert "performance.tbt_high" in finding_ids
    assert "performance.no_field_data" in finding_ids
    assert "performance.opportunity_available" in finding_ids
    assert "performance.no_lab_data" not in finding_ids
    assert result.summary.total_pages == 1
    assert result.summary.pages_with_lab_data == 1
    assert result.summary.pages_with_field_data == 0
    assert result.summary.poor_score_pages == 1
    assert result.summary.lcp_issue_pages == 1
    assert result.summary.cls_issue_pages == 1
    assert result.summary.inp_issue_pages == 1
    assert result.summary.tbt_issue_pages == 1
    assert result.summary.top_opportunities[0].id == "unused-javascript"

    lcp_finding = next(finding for finding in result.findings if finding.id == "performance.lcp_slow")
    assert lcp_finding.severity == Severity.HIGH
    assert lcp_finding.category == IssueCategory.PERFORMANCE


def test_run_performance_audit_flags_missing_lab_data_and_info_field_data():
    page = PagePerformanceSnapshot(page_url="https://example.com/no-data")

    result = run_performance_audit([page])

    assert [finding.id for finding in result.findings] == [
        "performance.no_lab_data",
        "performance.no_field_data",
    ]
    assert result.findings[0].severity == Severity.LOW
    assert result.findings[1].severity == Severity.INFO


def test_run_performance_audit_options_can_disable_noisy_checks():
    page = PagePerformanceSnapshot(
        page_url="https://example.com/",
        opportunities=[PerformanceOpportunity(id="render-blocking", title="Eliminate render-blocking resources", estimated_savings_ms=500)],
    )

    result = run_performance_audit(
        [page],
        options=PerformanceAuditOptions(
            flag_no_lab_data=False,
            flag_no_field_data=False,
            flag_opportunities=False,
        ),
    )

    assert result.findings == []
    assert result.summary.findings_total == 0


def test_performance_data_provider_can_be_faked_without_network():
    class FakeProvider:
        def fetch(self, url: str, strategy: str = "mobile") -> PagePerformanceSnapshot:
            assert strategy == "mobile"
            return PagePerformanceSnapshot(page_url=url, has_lab_data=True)

    provider: PerformanceDataProvider = FakeProvider()

    assert provider.fetch("https://example.com/").page_url == "https://example.com/"
