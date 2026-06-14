from __future__ import annotations

from collections import Counter

from geo_seo_engine.core.models import Evidence, IssueCategory, Severity
from geo_seo_engine.performance.models import (
    PagePerformanceSnapshot,
    PerformanceAuditFinding,
    PerformanceAuditOptions,
    PerformanceAuditResult,
    PerformanceAuditSummary,
    PerformanceMetric,
    PerformanceOpportunity,
)


def run_performance_audit(
    pages: list[PagePerformanceSnapshot],
    options: PerformanceAuditOptions | None = None,
    start_url: str | None = None,
) -> PerformanceAuditResult:
    audit_options = options or PerformanceAuditOptions()
    findings: list[PerformanceAuditFinding] = []

    for page in pages:
        if audit_options.flag_no_lab_data and not page.has_lab_data:
            findings.append(_no_lab_data_finding(page))
        if audit_options.flag_no_field_data and not page.has_field_data:
            findings.append(_no_field_data_finding(page))
        if page.performance_score is not None and page.performance_score < audit_options.low_score_threshold:
            findings.append(_low_score_finding(page, audit_options.low_score_threshold))

        lcp = _first_metric(page, "largest-contentful-paint")
        if lcp and lcp.value is not None and lcp.value > audit_options.lcp_warning_ms:
            findings.append(_lcp_slow_finding(page, lcp, audit_options))

        cls = _first_metric(page, "cumulative-layout-shift")
        if cls and cls.value is not None and cls.value > audit_options.cls_poor_threshold:
            findings.append(_cls_poor_finding(page, cls, audit_options.cls_poor_threshold))

        inp = _first_metric(page, "interaction-to-next-paint")
        if inp and inp.value is not None and inp.value > audit_options.inp_warning_ms:
            findings.append(_inp_slow_finding(page, inp, audit_options))

        tbt = _first_metric(page, "total-blocking-time")
        if tbt and tbt.value is not None and tbt.value > audit_options.tbt_high_ms:
            findings.append(_tbt_high_finding(page, tbt, audit_options.tbt_high_ms))

        if audit_options.flag_opportunities:
            findings.extend(_opportunity_findings(page, audit_options))

    return PerformanceAuditResult(
        start_url=start_url,
        pages=pages,
        findings=findings,
        summary=_build_summary(pages, findings, audit_options),
    )


def _low_score_finding(page: PagePerformanceSnapshot, threshold: float) -> PerformanceAuditFinding:
    return PerformanceAuditFinding(
        id="performance.low_score",
        title="Performance score is below the configured threshold",
        severity=Severity.MEDIUM,
        category=IssueCategory.PERFORMANCE,
        page_url=page.page_url,
        evidence=[Evidence(source="performance.score", value=page.performance_score, expected=threshold, observed=page.performance_score)],
        risk="Poor lab performance can correlate with slower user experience and weaker page experience signals.",
        recommendation="Review the slowest performance metrics and prioritize changes that improve user-perceived loading speed.",
        next_action=f"Inspect Lighthouse performance opportunities for {page.page_url}.",
        confidence=0.9,
    )


def _lcp_slow_finding(page: PagePerformanceSnapshot, metric: PerformanceMetric, options: PerformanceAuditOptions) -> PerformanceAuditFinding:
    severity = Severity.HIGH if metric.value and metric.value > options.lcp_poor_ms else Severity.MEDIUM
    return _metric_finding(
        page=page,
        metric=metric,
        finding_id="performance.lcp_slow",
        title="Largest Contentful Paint is slow",
        severity=severity,
        expected=options.lcp_warning_ms,
        risk="Slow LCP can make the main content feel delayed for users and may weaken page experience quality.",
        recommendation="Optimize the largest above-the-fold element, critical CSS, server response, image delivery, and render-blocking resources.",
    )


def _cls_poor_finding(page: PagePerformanceSnapshot, metric: PerformanceMetric, threshold: float) -> PerformanceAuditFinding:
    return _metric_finding(
        page=page,
        metric=metric,
        finding_id="performance.cls_poor",
        title="Cumulative Layout Shift is poor",
        severity=Severity.MEDIUM,
        expected=threshold,
        risk="Unexpected layout shifts can frustrate users and reduce perceived page quality.",
        recommendation="Reserve space for images, ads, embeds, and injected UI; avoid inserting content above existing content after load.",
    )


def _inp_slow_finding(page: PagePerformanceSnapshot, metric: PerformanceMetric, options: PerformanceAuditOptions) -> PerformanceAuditFinding:
    severity = Severity.HIGH if metric.value and metric.value > options.inp_poor_ms else Severity.MEDIUM
    return _metric_finding(
        page=page,
        metric=metric,
        finding_id="performance.inp_slow",
        title="Interaction to Next Paint is slow",
        severity=severity,
        expected=options.inp_warning_ms,
        risk="Slow INP can make interactions feel unresponsive for real users.",
        recommendation="Reduce long tasks, defer non-critical JavaScript, and profile event handlers on key interactions.",
    )


def _tbt_high_finding(page: PagePerformanceSnapshot, metric: PerformanceMetric, threshold: float) -> PerformanceAuditFinding:
    return _metric_finding(
        page=page,
        metric=metric,
        finding_id="performance.tbt_high",
        title="Total Blocking Time is high",
        severity=Severity.MEDIUM,
        expected=threshold,
        risk="High blocking time can delay interactivity in lab conditions and often points to heavy JavaScript execution.",
        recommendation="Split, defer, or remove non-critical JavaScript and reduce main-thread work during startup.",
    )


def _metric_finding(
    page: PagePerformanceSnapshot,
    metric: PerformanceMetric,
    finding_id: str,
    title: str,
    severity: Severity,
    expected: float,
    risk: str,
    recommendation: str,
) -> PerformanceAuditFinding:
    return PerformanceAuditFinding(
        id=finding_id,
        title=title,
        severity=severity,
        category=IssueCategory.PERFORMANCE,
        page_url=page.page_url,
        evidence=[Evidence(source=f"performance.{metric.category}.{metric.id}", value=metric.value, expected=expected, observed=metric.display_value or metric.value)],
        risk=risk,
        recommendation=recommendation,
        next_action=f"Prioritize fixes for {metric.label} on {page.page_url}.",
        confidence=0.9,
    )


def _no_lab_data_finding(page: PagePerformanceSnapshot) -> PerformanceAuditFinding:
    return PerformanceAuditFinding(
        id="performance.no_lab_data",
        title="No lab performance data was available",
        severity=Severity.LOW,
        category=IssueCategory.PERFORMANCE,
        page_url=page.page_url,
        evidence=[Evidence(source="performance.snapshot", value=False, expected=True, observed=page.has_lab_data)],
        risk="Without lab data, this audit cannot evaluate synthetic performance metrics for the page.",
        recommendation="Import a PageSpeed/Lighthouse-style JSON payload when lab performance analysis is needed.",
        next_action=f"Generate or provide a local performance payload for {page.page_url}.",
        confidence=1.0,
    )


def _no_field_data_finding(page: PagePerformanceSnapshot) -> PerformanceAuditFinding:
    return PerformanceAuditFinding(
        id="performance.no_field_data",
        title="No field performance data was available",
        severity=Severity.INFO,
        category=IssueCategory.PERFORMANCE,
        page_url=page.page_url,
        evidence=[Evidence(source="performance.snapshot", value=False, expected=True, observed=page.has_field_data)],
        risk="This is informational. Some pages or origins do not have enough public field data for Core Web Vitals reporting.",
        recommendation="Use lab data and your own analytics/RUM data when public field data is unavailable.",
        next_action=f"Confirm whether field data should exist for {page.page_url} before treating this as a gap.",
        confidence=1.0,
    )


def _opportunity_findings(page: PagePerformanceSnapshot, options: PerformanceAuditOptions) -> list[PerformanceAuditFinding]:
    findings: list[PerformanceAuditFinding] = []
    for opportunity in page.opportunities:
        if not _has_savings(opportunity):
            continue
        severity = _opportunity_severity(opportunity, options)
        findings.append(
            PerformanceAuditFinding(
                id="performance.opportunity_available",
                title=f"Performance opportunity available: {opportunity.title}",
                severity=severity,
                category=IssueCategory.PERFORMANCE,
                page_url=page.page_url,
                evidence=[
                    Evidence(
                        source=f"performance.opportunity.{opportunity.id}",
                        value=opportunity.estimated_savings_ms or opportunity.estimated_savings_bytes,
                        observed=_opportunity_observed(opportunity),
                    )
                ],
                risk="Known performance opportunities can point to avoidable latency, transfer size, or main-thread work.",
                recommendation=opportunity.description or "Review the opportunity and prioritize it against user impact and implementation effort.",
                next_action=f"Evaluate the '{opportunity.title}' opportunity for {page.page_url}.",
                confidence=0.85,
            )
        )
    return findings


def _build_summary(
    pages: list[PagePerformanceSnapshot],
    findings: list[PerformanceAuditFinding],
    options: PerformanceAuditOptions,
) -> PerformanceAuditSummary:
    by_severity = Counter(str(finding.severity) for finding in findings)
    by_category = Counter(str(finding.category) for finding in findings)

    return PerformanceAuditSummary(
        total_pages=len(pages),
        pages_with_lab_data=sum(1 for page in pages if page.has_lab_data),
        pages_with_field_data=sum(1 for page in pages if page.has_field_data),
        findings_total=len(findings),
        by_severity=dict(sorted(by_severity.items())),
        by_category=dict(sorted(by_category.items())),
        poor_score_pages=sum(1 for page in pages if page.performance_score is not None and page.performance_score < options.low_score_threshold),
        lcp_issue_pages=sum(1 for page in pages if _metric_value(page, "largest-contentful-paint") is not None and _metric_value(page, "largest-contentful-paint") > options.lcp_warning_ms),
        cls_issue_pages=sum(1 for page in pages if _metric_value(page, "cumulative-layout-shift") is not None and _metric_value(page, "cumulative-layout-shift") > options.cls_poor_threshold),
        inp_issue_pages=sum(1 for page in pages if _metric_value(page, "interaction-to-next-paint") is not None and _metric_value(page, "interaction-to-next-paint") > options.inp_warning_ms),
        tbt_issue_pages=sum(1 for page in pages if _metric_value(page, "total-blocking-time") is not None and _metric_value(page, "total-blocking-time") > options.tbt_high_ms),
        top_opportunities=_top_opportunities(pages),
    )


def _first_metric(page: PagePerformanceSnapshot, metric_id: str) -> PerformanceMetric | None:
    return next((metric for metric in page.metrics if metric.id == metric_id), None)


def _metric_value(page: PagePerformanceSnapshot, metric_id: str) -> float | None:
    metric = _first_metric(page, metric_id)
    return metric.value if metric else None


def _has_savings(opportunity: PerformanceOpportunity) -> bool:
    return bool(opportunity.estimated_savings_ms or opportunity.estimated_savings_bytes)


def _opportunity_severity(opportunity: PerformanceOpportunity, options: PerformanceAuditOptions) -> Severity:
    if (opportunity.estimated_savings_ms or 0) >= options.opportunity_medium_savings_ms:
        return Severity.MEDIUM
    if (opportunity.estimated_savings_bytes or 0) >= options.opportunity_medium_savings_bytes:
        return Severity.MEDIUM
    return Severity.LOW


def _opportunity_observed(opportunity: PerformanceOpportunity) -> str:
    return f"savings_ms={opportunity.estimated_savings_ms}, savings_bytes={opportunity.estimated_savings_bytes}"


def _top_opportunities(pages: list[PagePerformanceSnapshot]) -> list[PerformanceOpportunity]:
    opportunities = [opportunity for page in pages for opportunity in page.opportunities if _has_savings(opportunity)]
    return sorted(
        opportunities,
        key=lambda item: (item.estimated_savings_ms or 0, item.estimated_savings_bytes or 0),
        reverse=True,
    )[:5]
