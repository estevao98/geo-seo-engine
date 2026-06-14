from __future__ import annotations

from pydantic import Field

from geo_seo_engine.content import ExtractedMainContent
from geo_seo_engine.core.models import CoreModel, Evidence, IssueCategory, Severity


class ContentQualityAuditOptions(CoreModel):
    thin_content_word_threshold: int = Field(default=300, ge=0)
    low_paragraph_threshold: int = Field(default=2, ge=0)
    high_link_density_threshold: float = Field(default=0.2, ge=0.0)
    low_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    min_meta_alignment_overlap: float = Field(default=0.2, ge=0.0, le=1.0)
    flag_title_h1_mismatch: bool = True
    flag_meta_description_misaligned: bool = True
    flag_weak_heading_structure: bool = True
    flag_boilerplate_heavy_extraction: bool = True


class ContentQualityFinding(CoreModel):
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


class ContentQualitySummary(CoreModel):
    total_pages: int = Field(default=0, ge=0)
    findings_total: int = Field(default=0, ge=0)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    thin_content_pages: int = Field(default=0, ge=0)
    missing_h1_pages: int = Field(default=0, ge=0)
    multiple_h1_pages: int = Field(default=0, ge=0)
    missing_title_pages: int = Field(default=0, ge=0)
    missing_meta_description_pages: int = Field(default=0, ge=0)
    high_link_density_pages: int = Field(default=0, ge=0)
    low_confidence_pages: int = Field(default=0, ge=0)


class ContentQualityAuditResult(CoreModel):
    start_url: str | None = None
    pages: list[ExtractedMainContent] = Field(default_factory=list)
    findings: list[ContentQualityFinding] = Field(default_factory=list)
    summary: ContentQualitySummary
