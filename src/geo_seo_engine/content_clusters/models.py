from __future__ import annotations

from typing import Literal

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence


ClusterPriority = Literal["critical", "high", "medium", "low"]


class ContentClusterSourceRef(CoreModel):
    source_type: Literal["page", "brief", "opportunity", "finding", "search_console", "internal_link"]
    source_id: str
    page_url: str | None = None


class ContentClusterLinkRecommendation(CoreModel):
    source_url: str
    target_url: str
    anchor_text: str | None = None
    reason: str
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ContentCluster(CoreModel):
    id: str
    label: str
    pillar_page_url: str | None = None
    pillar_reason: str | None = None
    supporting_page_urls: list[str] = Field(default_factory=list)
    supporting_brief_ids: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    internal_link_recommendations: list[ContentClusterLinkRecommendation] = Field(default_factory=list)
    source_refs: list[ContentClusterSourceRef] = Field(default_factory=list)
    source_page_ids: list[str] = Field(default_factory=list)
    source_brief_ids: list[str] = Field(default_factory=list)
    source_opportunity_ids: list[str] = Field(default_factory=list)
    source_finding_ids: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)


class ContentClusterSummary(CoreModel):
    total_clusters: int = Field(default=0, ge=0)
    total_pages: int = Field(default=0, ge=0)
    total_briefs: int = Field(default=0, ge=0)
    total_link_recommendations: int = Field(default=0, ge=0)
    by_priority: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    inputs_present: list[str] = Field(default_factory=list)
    inputs_missing: list[str] = Field(default_factory=list)


class ContentClusterPlannerResult(CoreModel):
    clusters: list[ContentCluster] = Field(default_factory=list)
    summary: ContentClusterSummary
