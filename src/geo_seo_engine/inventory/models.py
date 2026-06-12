from __future__ import annotations

from pydantic import Field

from geo_seo_engine.core.models import CoreModel


class InventoryUrl(CoreModel):
    url: str
    normalized_url: str
    final_url: str
    status_code: int
    depth: int
    content_type: str | None = None
    is_html: bool
    is_success: bool
    is_redirected: bool
    has_error: bool
    error: str | None = None
    discovered_from: str | None = None
    links_found: int = 0


class InventorySkippedUrl(CoreModel):
    url: str
    reason: str
    source_url: str | None = None


class InventorySummary(CoreModel):
    total_pages: int = Field(default=0, ge=0)
    html_pages: int = Field(default=0, ge=0)
    non_html_pages: int = Field(default=0, ge=0)
    success_pages: int = Field(default=0, ge=0)
    redirected_pages: int = Field(default=0, ge=0)
    error_pages: int = Field(default=0, ge=0)
    skipped_urls: int = Field(default=0, ge=0)
    max_depth: int = Field(default=0, ge=0)
    max_pages_reached: bool = False
    status_code_counts: dict[str, int] = Field(default_factory=dict)
    content_type_counts: dict[str, int] = Field(default_factory=dict)


class InventoryResult(CoreModel):
    start_url: str
    urls: list[InventoryUrl] = Field(default_factory=list)
    skipped_urls: list[InventorySkippedUrl] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    summary: InventorySummary
