from __future__ import annotations

from pydantic import Field

from geo_seo_engine.content import ExtractedMainContent
from geo_seo_engine.core.models import CoreModel, Evidence, IssueCategory, Severity


class EntityReadinessAuditOptions(CoreModel):
    min_topic_token_overlap: float = Field(default=0.2, ge=0.0, le=1.0)
    min_content_word_count: int = Field(default=50, ge=0)


class EntityStructuredDataSignal(CoreModel):
    types: list[str] = Field(default_factory=list)
    names: list[str] = Field(default_factory=list)
    authors: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)
    same_as: list[str] = Field(default_factory=list)
    has_organization: bool = False
    has_person: bool = False
    has_article: bool = False
    has_web_page: bool = False
    has_breadcrumb_list: bool = False


class EntityReadinessPageAudit(CoreModel):
    page_url: str
    primary_entity: str | None = None
    topic_terms: list[str] = Field(default_factory=list)
    visible_authorship_signals: list[str] = Field(default_factory=list)
    visible_organization_signals: list[str] = Field(default_factory=list)
    structured_data: EntityStructuredDataSignal = Field(default_factory=EntityStructuredDataSignal)
    title_h1_aligned: bool | None = None
    meta_content_aligned: bool | None = None
    structured_data_content_aligned: bool | None = None


class EntityReadinessFinding(CoreModel):
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


class EntityReadinessSummary(CoreModel):
    total_pages: int = Field(default=0, ge=0)
    findings_total: int = Field(default=0, ge=0)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    pages_with_primary_entity: int = Field(default=0, ge=0)
    pages_with_author_signal: int = Field(default=0, ge=0)
    pages_with_publisher_signal: int = Field(default=0, ge=0)
    pages_with_same_as_signal: int = Field(default=0, ge=0)
    pages_with_article_schema: int = Field(default=0, ge=0)
    pages_with_web_page_schema: int = Field(default=0, ge=0)
    pages_with_breadcrumb_schema: int = Field(default=0, ge=0)
    average_readiness_score: float = Field(default=0.0, ge=0.0, le=100.0)


class EntityReadinessAuditResult(CoreModel):
    start_url: str | None = None
    pages: list[ExtractedMainContent] = Field(default_factory=list)
    page_audits: list[EntityReadinessPageAudit] = Field(default_factory=list)
    findings: list[EntityReadinessFinding] = Field(default_factory=list)
    summary: EntityReadinessSummary
