from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(StrEnum):
    TECHNICAL = "technical"
    CRAWLABILITY = "crawlability"
    INDEXABILITY = "indexability"
    STRUCTURED_DATA = "structured_data"
    CONTENT = "content"
    ENTITY = "entity"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REPORTING = "reporting"


class CoreModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class Evidence(CoreModel):
    source: str
    selector: str | None = None
    value: str | int | float | bool | None = None
    expected: str | int | float | bool | None = None
    observed: str | int | float | bool | None = None


class Recommendation(CoreModel):
    issue_id: str
    action: str
    rationale: str
    effort: str | None = None
    impact: str | None = None
    owner: str | None = None


class Issue(CoreModel):
    id: str
    title: str
    category: IssueCategory
    severity: Severity
    url: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    risk: str | None = None
    recommendation: Recommendation | None = None
    next_action: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class UrlIdentity(CoreModel):
    raw_url: str
    normalized_url: str
    final_url: str | None = None
    canonical_url: str | None = None
    host: str | None = None
    path: str | None = None


class ScoreSummary(CoreModel):
    score: int | None = Field(default=None, ge=0, le=100)
    max_score: int = Field(default=100, ge=1)
    by_severity: dict[str, int] = Field(default_factory=dict)


class AuditSummary(CoreModel):
    total_issues: int = Field(default=0, ge=0)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    score: ScoreSummary | None = None


class AuditRun(CoreModel):
    id: str
    started_at: datetime
    tool_version: str
    target: UrlIdentity
    issues: list[Issue] = Field(default_factory=list)
    summary: AuditSummary
