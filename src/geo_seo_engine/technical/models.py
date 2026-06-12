from __future__ import annotations

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence, IssueCategory, Severity


class TechnicalAuditOptions(CoreModel):
    max_depth_warning: int = Field(default=3, ge=0)
    high_skipped_urls_warning: int = Field(default=25, ge=0)
    flag_non_html: bool = True
    flag_redirects: bool = True
    flag_zero_links: bool = True


class TechnicalAuditFinding(CoreModel):
    id: str
    title: str
    severity: Severity
    category: IssueCategory
    url: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    risk: str
    recommendation: str
    next_action: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class TechnicalAuditSummary(CoreModel):
    total_findings: int = Field(default=0, ge=0)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)


class TechnicalAuditResult(CoreModel):
    start_url: str
    findings: list[TechnicalAuditFinding] = Field(default_factory=list)
    summary: TechnicalAuditSummary
