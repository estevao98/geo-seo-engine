from __future__ import annotations

from typing import Literal

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence


BriefPriority = Literal["critical", "high", "medium", "low"]
BriefType = Literal["new_page", "page_refresh", "risk_remediation"]


class ContentBriefLinkOpportunity(CoreModel):
    source_url: str | None = None
    target_url: str
    anchor_text: str | None = None
    reason: str
    source_finding_id: str | None = None


class ContentBriefRiskAction(CoreModel):
    source_id: str
    source_type: Literal["opportunity", "finding"]
    risk: str | None = None
    next_action: str
    evidence: list[Evidence] = Field(default_factory=list)


class ContentBrief(CoreModel):
    id: str
    target_url: str | None = None
    proposed_url: str | None = None
    brief_type: BriefType
    priority: BriefPriority
    primary_topic_entity_cue: str | None = None
    search_intent_cue: str | None = None
    audience_usefulness_notes: list[str] = Field(default_factory=list)
    required_sections: list[str] = Field(default_factory=list)
    content_gaps: list[str] = Field(default_factory=list)
    questions_to_answer: list[str] = Field(default_factory=list)
    internal_link_opportunities: list[ContentBriefLinkOpportunity] = Field(default_factory=list)
    risks_and_next_actions: list[ContentBriefRiskAction] = Field(default_factory=list)
    source_opportunity_ids: list[str] = Field(default_factory=list)
    source_finding_ids: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)


class ContentBriefSummary(CoreModel):
    total_briefs: int = Field(default=0, ge=0)
    by_priority: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    inputs_present: list[str] = Field(default_factory=list)
    inputs_missing: list[str] = Field(default_factory=list)


class ContentBriefGeneratorResult(CoreModel):
    briefs: list[ContentBrief] = Field(default_factory=list)
    summary: ContentBriefSummary
