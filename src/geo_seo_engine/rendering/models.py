from __future__ import annotations

from typing import Literal

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence, IssueCategory, Severity


RenderStatus = Literal["rendered", "error", "timeout", "skipped"]


class RenderedPage(CoreModel):
    page_url: str
    html: str | None = None
    status: RenderStatus = "rendered"
    error: str | None = None


class PageRenderSnapshot(CoreModel):
    page_url: str
    static_html: str
    rendered_html: str | None = None
    static_title: str | None = None
    rendered_title: str | None = None
    static_meta_description: str | None = None
    rendered_meta_description: str | None = None
    static_canonical: str | None = None
    rendered_canonical: str | None = None
    static_robots: str | None = None
    rendered_robots: str | None = None
    static_links: list[str] = Field(default_factory=list)
    rendered_links: list[str] = Field(default_factory=list)
    static_text_length: int = Field(default=0, ge=0)
    rendered_text_length: int = Field(default=0, ge=0)
    static_script_count: int = Field(default=0, ge=0)
    render_status: RenderStatus = "rendered"
    render_error: str | None = None


class RenderingAuditOptions(CoreModel):
    flag_title_changed: bool = True
    flag_meta_description_changed: bool = True
    flag_canonical_changed: bool = True
    flag_robots_changed: bool = True
    flag_links_added_by_js: bool = True
    flag_static_content_sparse: bool = True
    flag_content_only_after_render: bool = True
    flag_rendered_noindex: bool = True
    static_sparse_text_threshold: int = Field(default=80, ge=0)
    rendered_populated_text_threshold: int = Field(default=300, ge=0)
    min_added_links_warning: int = Field(default=3, ge=1)
    link_added_ratio_warning: float = Field(default=0.25, ge=0.0)


class RenderingAuditFinding(CoreModel):
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


class RenderingAuditSummary(CoreModel):
    total_pages: int = Field(default=0, ge=0)
    rendered_pages: int = Field(default=0, ge=0)
    render_errors: int = Field(default=0, ge=0)
    findings_total: int = Field(default=0, ge=0)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    pages_title_changed: int = Field(default=0, ge=0)
    pages_description_changed: int = Field(default=0, ge=0)
    pages_canonical_changed: int = Field(default=0, ge=0)
    pages_robots_changed: int = Field(default=0, ge=0)
    pages_links_added_by_js: int = Field(default=0, ge=0)
    pages_static_sparse_rendered_content: int = Field(default=0, ge=0)


class RenderingAuditResult(CoreModel):
    start_url: str | None = None
    pages: list[PageRenderSnapshot] = Field(default_factory=list)
    findings: list[RenderingAuditFinding] = Field(default_factory=list)
    summary: RenderingAuditSummary
