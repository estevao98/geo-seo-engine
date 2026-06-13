from __future__ import annotations

from typing import Literal

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence, IssueCategory, Severity


class SocialMetaTag(CoreModel):
    page_url: str
    kind: Literal["og", "twitter", "other"]
    key: str
    raw_key: str
    content: str
    attribute_name: Literal["property", "name"]
    is_empty: bool


class SocialImageReference(CoreModel):
    page_url: str
    metadata_key: str
    raw_url: str
    resolved_url: str | None = None
    normalized_url: str | None = None
    is_relative: bool = False
    is_external: bool = False
    is_invalid: bool = False
    is_data_uri: bool = False


class PageSocialMetadata(CoreModel):
    page_url: str
    tags: list[SocialMetaTag] = Field(default_factory=list)
    open_graph: dict[str, str] = Field(default_factory=dict)
    twitter: dict[str, str] = Field(default_factory=dict)
    duplicates: dict[str, int] = Field(default_factory=dict)
    image_references: list[SocialImageReference] = Field(default_factory=list)
    used_open_graph_fallback_fields: list[str] = Field(default_factory=list)


class SocialAuditOptions(CoreModel):
    flag_open_graph: bool = True
    flag_twitter: bool = True
    flag_empty_content: bool = True
    flag_duplicates: bool = True
    flag_relative_image_url: bool = True
    flag_external_image_host: bool = True
    allow_twitter_og_fallback: bool = True


class SocialAuditFinding(CoreModel):
    id: str
    title: str
    severity: Severity
    category: IssueCategory
    page_url: str
    metadata_key: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    risk: str
    recommendation: str
    next_action: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class SocialAuditSummary(CoreModel):
    total_pages: int = Field(default=0, ge=0)
    findings_total: int = Field(default=0, ge=0)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    pages_missing_og_title: int = Field(default=0, ge=0)
    pages_missing_og_description: int = Field(default=0, ge=0)
    pages_missing_og_image: int = Field(default=0, ge=0)
    pages_missing_og_url: int = Field(default=0, ge=0)
    pages_missing_twitter_card: int = Field(default=0, ge=0)
    duplicate_tag_pages: int = Field(default=0, ge=0)
    empty_content_tags: int = Field(default=0, ge=0)
    external_social_images: int = Field(default=0, ge=0)
    relative_social_images: int = Field(default=0, ge=0)
    invalid_social_images: int = Field(default=0, ge=0)


class SocialAuditResult(CoreModel):
    start_url: str | None = None
    pages: list[PageSocialMetadata] = Field(default_factory=list)
    findings: list[SocialAuditFinding] = Field(default_factory=list)
    summary: SocialAuditSummary
