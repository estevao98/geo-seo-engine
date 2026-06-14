from __future__ import annotations

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence, IssueCategory, Severity


class InternalLinkGraphOptions(CoreModel):
    near_orphan_inbound_threshold: int = Field(default=1, ge=0)
    hub_outbound_threshold: int = Field(default=5, ge=1)
    overly_deep_threshold: int = Field(default=3, ge=0)
    repeated_anchor_target_threshold: int = Field(default=2, ge=2)
    weak_anchor_diversity_threshold: int = Field(default=2, ge=1)
    generic_anchor_texts: list[str] = Field(
        default_factory=lambda: [
            "click here",
            "here",
            "learn more",
            "more",
            "read more",
            "see more",
            "this page",
            "link",
        ]
    )


class InternalLinkEdge(CoreModel):
    source_url: str
    target_url: str
    anchor_text: str | None = None
    source_depth: int = Field(default=0, ge=0)
    target_crawled: bool = False


class InternalLinkPageMetrics(CoreModel):
    url: str
    normalized_url: str
    final_url: str | None = None
    status_code: int | None = None
    depth: int = Field(default=0, ge=0)
    discovered_from: str | None = None
    inbound_internal_links: int = Field(default=0, ge=0)
    outbound_internal_links: int = Field(default=0, ge=0)
    unique_inbound_sources: int = Field(default=0, ge=0)
    unique_outbound_targets: int = Field(default=0, ge=0)
    inbound_anchor_texts: list[str] = Field(default_factory=list)
    outbound_anchor_texts: list[str] = Field(default_factory=list)
    is_start_url: bool = False
    is_orphan: bool = False
    is_near_orphan: bool = False
    is_leaf: bool = False
    is_hub: bool = False
    is_weakly_connected: bool = False
    has_extracted_content: bool = False


class InternalLinkGraphFinding(CoreModel):
    id: str
    title: str
    severity: Severity
    category: IssueCategory
    page_url: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    risk: str
    recommendation: str
    next_action: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class InternalLinkGraphSummary(CoreModel):
    total_pages: int = Field(default=0, ge=0)
    crawled_pages: int = Field(default=0, ge=0)
    discovered_urls: int = Field(default=0, ge=0)
    extracted_content_pages: int = Field(default=0, ge=0)
    internal_edges: int = Field(default=0, ge=0)
    discovered_not_crawled_count: int = Field(default=0, ge=0)
    crawled_not_discovered_count: int = Field(default=0, ge=0)
    orphan_pages: int = Field(default=0, ge=0)
    near_orphan_pages: int = Field(default=0, ge=0)
    leaf_pages: int = Field(default=0, ge=0)
    hub_pages: int = Field(default=0, ge=0)
    weakly_connected_pages: int = Field(default=0, ge=0)
    max_depth: int = Field(default=0, ge=0)
    overly_deep_pages: int = Field(default=0, ge=0)
    generic_anchor_count: int = Field(default=0, ge=0)
    missing_anchor_count: int = Field(default=0, ge=0)
    repeated_anchor_texts: dict[str, int] = Field(default_factory=dict)
    findings_total: int = Field(default=0, ge=0)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)


class InternalLinkGraphAuditResult(CoreModel):
    start_url: str | None = None
    pages: list[InternalLinkPageMetrics] = Field(default_factory=list)
    edges: list[InternalLinkEdge] = Field(default_factory=list)
    findings: list[InternalLinkGraphFinding] = Field(default_factory=list)
    summary: InternalLinkGraphSummary
