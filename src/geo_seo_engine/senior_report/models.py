from __future__ import annotations

from typing import Literal

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence


ReportPriority = Literal["critical", "high", "medium", "low", "info"]


class SeniorReportCoverageItem(CoreModel):
    input_name: str
    present: bool
    item_count: int = Field(default=0, ge=0)
    limitation: str | None = None


class SeniorReportSummary(CoreModel):
    headline: str
    available_inputs: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    total_findings: int = Field(default=0, ge=0)
    total_opportunities: int = Field(default=0, ge=0)
    total_operational_actions: int = Field(default=0, ge=0)
    top_priority: ReportPriority | None = None
    statements: list[str] = Field(default_factory=list)


class SeniorHealthSnapshot(CoreModel):
    technical_findings: int = Field(default=0, ge=0)
    content_quality_findings: int = Field(default=0, ge=0)
    entity_readiness_findings: int = Field(default=0, ge=0)
    internal_link_findings: int = Field(default=0, ge=0)
    opportunity_count: int = Field(default=0, ge=0)
    content_brief_count: int = Field(default=0, ge=0)
    content_cluster_count: int = Field(default=0, ge=0)
    ai_readiness_targets: int = Field(default=0, ge=0)
    ai_readiness_average_score: float | None = Field(default=None, ge=0.0, le=100.0)
    search_console_rows: int = Field(default=0, ge=0)
    by_severity: dict[str, int] = Field(default_factory=dict)


class SeniorPriorityRisk(CoreModel):
    id: str
    source: str
    title: str
    priority: ReportPriority
    risk: str | None = None
    next_action: str | None = None
    page_url: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class SeniorOpportunitySummary(CoreModel):
    total_opportunities: int = Field(default=0, ge=0)
    by_priority: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    top_opportunity_ids: list[str] = Field(default_factory=list)
    remediation_themes: list[str] = Field(default_factory=list)


class SeniorAIReadinessSummary(CoreModel):
    targets: int = Field(default=0, ge=0)
    average_score: float | None = Field(default=None, ge=0.0, le=100.0)
    by_readiness_band: dict[str, int] = Field(default_factory=dict)
    by_priority: dict[str, int] = Field(default_factory=dict)
    explicit_limitations: list[str] = Field(default_factory=list)


class SeniorClusterContentSummary(CoreModel):
    total_clusters: int = Field(default=0, ge=0)
    total_briefs: int = Field(default=0, ge=0)
    total_link_recommendations: int = Field(default=0, ge=0)
    cluster_ids: list[str] = Field(default_factory=list)
    brief_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class SeniorOperationalAction(CoreModel):
    id: str
    priority: ReportPriority
    source: str
    action: str
    page_url: str | None = None
    risk: str | None = None
    owner_hint: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class SeniorEvidenceReference(CoreModel):
    source: str
    source_id: str | None = None
    page_url: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class SeniorReportResult(CoreModel):
    report_type: Literal["senior_executive_operational"] = "senior_executive_operational"
    executive_summary: SeniorReportSummary
    health_readiness_snapshot: SeniorHealthSnapshot
    top_risks_and_priorities: list[SeniorPriorityRisk] = Field(default_factory=list)
    input_coverage: list[SeniorReportCoverageItem] = Field(default_factory=list)
    opportunity_and_remediation_summary: SeniorOpportunitySummary
    ai_geo_readiness_summary: SeniorAIReadinessSummary
    cluster_and_content_planning_summary: SeniorClusterContentSummary
    operational_action_queue: list[SeniorOperationalAction] = Field(default_factory=list)
    evidence_source_references: list[SeniorEvidenceReference] = Field(default_factory=list)
    limitations_and_assumptions: list[str] = Field(default_factory=list)
