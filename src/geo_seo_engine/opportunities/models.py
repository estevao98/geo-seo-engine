from __future__ import annotations

from typing import Literal

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence


OpportunityPriority = Literal["critical", "high", "medium", "low"]


class OpportunityScoreComponents(CoreModel):
    severity: float = Field(default=0.0, ge=0.0)
    impact: float = Field(default=0.0, ge=0.0)
    effort: float = Field(default=0.0, ge=0.0)
    confidence: float = Field(default=0.0, ge=0.0)
    analytics: float = Field(default=0.0, ge=0.0)
    total: float = Field(default=0.0, ge=0.0, le=100.0)


class OpportunityAnalyticsSignal(CoreModel):
    impressions: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    ctr: float = Field(default=0.0, ge=0.0, le=1.0)
    position: float = Field(default=0.0, ge=0.0)


class Opportunity(CoreModel):
    id: str
    finding_id: str
    source: str
    type: str
    page_url: str | None = None
    title: str
    severity: str
    impact: str
    effort: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    priority: OpportunityPriority
    score: float = Field(ge=0.0, le=100.0)
    score_components: OpportunityScoreComponents
    rationale: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    risk: str | None = None
    next_action: str
    analytics: OpportunityAnalyticsSignal | None = None


class OpportunityBucket(CoreModel):
    group_by: Literal["page", "type", "priority"]
    key: str
    count: int = Field(ge=0)
    max_score: float = Field(ge=0.0, le=100.0)
    average_score: float = Field(ge=0.0, le=100.0)
    opportunity_ids: list[str] = Field(default_factory=list)


class OpportunitySummary(CoreModel):
    total_opportunities: int = Field(default=0, ge=0)
    by_priority: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_page: dict[str, int] = Field(default_factory=dict)
    top_opportunity_ids: list[str] = Field(default_factory=list)
    inputs_present: list[str] = Field(default_factory=list)
    inputs_missing: list[str] = Field(default_factory=list)


class OpportunityEngineResult(CoreModel):
    opportunities: list[Opportunity] = Field(default_factory=list)
    buckets_by_page: list[OpportunityBucket] = Field(default_factory=list)
    buckets_by_type: list[OpportunityBucket] = Field(default_factory=list)
    buckets_by_priority: list[OpportunityBucket] = Field(default_factory=list)
    summary: OpportunitySummary
