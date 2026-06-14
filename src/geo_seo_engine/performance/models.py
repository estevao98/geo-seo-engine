from __future__ import annotations

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence, IssueCategory, Severity


class PerformanceMetric(CoreModel):
    id: str
    label: str
    value: float | None = None
    unit: str | None = None
    display_value: str | None = None
    category: str = "lab"
    source: str = "lighthouse"


class PerformanceOpportunity(CoreModel):
    id: str
    title: str
    description: str | None = None
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    estimated_savings_ms: float | None = Field(default=None, ge=0.0)
    estimated_savings_bytes: float | None = Field(default=None, ge=0.0)


class PagePerformanceSnapshot(CoreModel):
    page_url: str
    requested_url: str | None = None
    final_url: str | None = None
    strategy: str = "mobile"
    source: str = "pagespeed"
    performance_score: float | None = Field(default=None, ge=0.0, le=100.0)
    metrics: list[PerformanceMetric] = Field(default_factory=list)
    opportunities: list[PerformanceOpportunity] = Field(default_factory=list)
    diagnostics: list[PerformanceOpportunity] = Field(default_factory=list)
    has_lab_data: bool = False
    has_field_data: bool = False
    raw_source_version: str | None = None


class PerformanceAuditOptions(CoreModel):
    low_score_threshold: float = Field(default=50.0, ge=0.0, le=100.0)
    lcp_warning_ms: float = Field(default=2500.0, ge=0.0)
    lcp_poor_ms: float = Field(default=4000.0, ge=0.0)
    cls_poor_threshold: float = Field(default=0.25, ge=0.0)
    inp_warning_ms: float = Field(default=200.0, ge=0.0)
    inp_poor_ms: float = Field(default=500.0, ge=0.0)
    tbt_high_ms: float = Field(default=300.0, ge=0.0)
    opportunity_medium_savings_ms: float = Field(default=1000.0, ge=0.0)
    opportunity_medium_savings_bytes: float = Field(default=500_000.0, ge=0.0)
    flag_no_lab_data: bool = True
    flag_no_field_data: bool = True
    flag_opportunities: bool = True


class PerformanceAuditFinding(CoreModel):
    id: str
    title: str
    severity: Severity
    category: IssueCategory
    page_url: str
    evidence: list[Evidence] = Field(default_factory=list)
    risk: str
    recommendation: str
    next_action: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class PerformanceAuditSummary(CoreModel):
    total_pages: int = Field(default=0, ge=0)
    pages_with_lab_data: int = Field(default=0, ge=0)
    pages_with_field_data: int = Field(default=0, ge=0)
    findings_total: int = Field(default=0, ge=0)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    poor_score_pages: int = Field(default=0, ge=0)
    lcp_issue_pages: int = Field(default=0, ge=0)
    cls_issue_pages: int = Field(default=0, ge=0)
    inp_issue_pages: int = Field(default=0, ge=0)
    tbt_issue_pages: int = Field(default=0, ge=0)
    top_opportunities: list[PerformanceOpportunity] = Field(default_factory=list)


class PerformanceAuditResult(CoreModel):
    start_url: str | None = None
    pages: list[PagePerformanceSnapshot] = Field(default_factory=list)
    findings: list[PerformanceAuditFinding] = Field(default_factory=list)
    summary: PerformanceAuditSummary
