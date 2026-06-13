from __future__ import annotations

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence, IssueCategory, Severity


class ImageSrcsetCandidate(CoreModel):
    raw_url: str
    descriptor: str | None = None


class ImageResource(CoreModel):
    page_url: str
    raw_src: str
    resolved_src: str
    normalized_src: str
    alt: str | None = None
    has_alt_attribute: bool = False
    width: str | None = None
    height: str | None = None
    loading: str | None = None
    srcset: str | None = None
    srcset_candidates: list[ImageSrcsetCandidate] = Field(default_factory=list)
    is_decorative: bool = False
    is_data_uri: bool = False
    is_external: bool = False


class SkippedImage(CoreModel):
    page_url: str
    reason: str
    raw_src: str | None = None


class PageImageInventory(CoreModel):
    page_url: str
    images: list[ImageResource] = Field(default_factory=list)
    skipped_images: list[SkippedImage] = Field(default_factory=list)


class ImageAuditOptions(CoreModel):
    flag_missing_alt: bool = True
    flag_empty_alt: bool = True
    flag_missing_dimensions: bool = True
    flag_external_images: bool = True
    flag_data_uri: bool = True
    flag_missing_lazy_loading: bool = False


class ImageAuditFinding(CoreModel):
    id: str
    title: str
    severity: Severity
    category: IssueCategory
    page_url: str
    image_url: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    risk: str
    recommendation: str
    next_action: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ImageAuditSummary(CoreModel):
    total_pages: int = Field(default=0, ge=0)
    total_images: int = Field(default=0, ge=0)
    findings_total: int = Field(default=0, ge=0)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    missing_src_images: int = Field(default=0, ge=0)
    missing_alt_images: int = Field(default=0, ge=0)
    empty_alt_images: int = Field(default=0, ge=0)
    missing_dimension_images: int = Field(default=0, ge=0)
    external_images: int = Field(default=0, ge=0)
    data_uri_images: int = Field(default=0, ge=0)
    decorative_images: int = Field(default=0, ge=0)


class ImageAuditResult(CoreModel):
    start_url: str | None = None
    pages: list[PageImageInventory] = Field(default_factory=list)
    findings: list[ImageAuditFinding] = Field(default_factory=list)
    summary: ImageAuditSummary
