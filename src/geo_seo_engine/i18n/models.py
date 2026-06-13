from __future__ import annotations

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence, IssueCategory, Severity


class HreflangLink(CoreModel):
    page_url: str
    raw_hreflang: str
    normalized_hreflang: str | None = None
    raw_href: str
    resolved_url: str
    normalized_url: str
    is_self_reference: bool = False
    is_x_default: bool = False
    is_relative: bool = False
    is_external: bool = False
    is_invalid_url: bool = False
    is_invalid_hreflang: bool = False
    is_non_http: bool = False


class SkippedHreflangLink(CoreModel):
    page_url: str
    reason: str
    raw_hreflang: str | None = None
    raw_href: str | None = None


class PageHreflangInventory(CoreModel):
    page_url: str
    links: list[HreflangLink] = Field(default_factory=list)
    skipped_links: list[SkippedHreflangLink] = Field(default_factory=list)
    duplicates: dict[str, int] = Field(default_factory=dict)


class HreflangAuditOptions(CoreModel):
    flag_missing_self_reference: bool = True
    flag_missing_href: bool = True
    flag_missing_hreflang: bool = True
    flag_invalid_hreflang: bool = True
    flag_invalid_url: bool = True
    flag_relative_url: bool = True
    flag_duplicate_values: bool = True
    flag_external_hosts: bool = True
    flag_missing_reciprocal: bool = True
    flag_missing_x_default: bool = False


class HreflangAuditFinding(CoreModel):
    id: str
    title: str
    severity: Severity
    category: IssueCategory
    page_url: str
    hreflang: str | None = None
    target_url: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    risk: str
    recommendation: str
    next_action: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class HreflangAuditSummary(CoreModel):
    total_pages: int = Field(default=0, ge=0)
    total_links: int = Field(default=0, ge=0)
    findings_total: int = Field(default=0, ge=0)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    pages_missing_self_reference: int = Field(default=0, ge=0)
    pages_with_x_default: int = Field(default=0, ge=0)
    duplicate_hreflang_pages: int = Field(default=0, ge=0)
    invalid_hreflang_links: int = Field(default=0, ge=0)
    invalid_url_links: int = Field(default=0, ge=0)
    relative_url_links: int = Field(default=0, ge=0)
    external_url_links: int = Field(default=0, ge=0)
    missing_reciprocal_links: int = Field(default=0, ge=0)


class HreflangAuditResult(CoreModel):
    start_url: str | None = None
    pages: list[PageHreflangInventory] = Field(default_factory=list)
    findings: list[HreflangAuditFinding] = Field(default_factory=list)
    summary: HreflangAuditSummary
