from __future__ import annotations

from pydantic import Field

from geo_seo_engine.core.models import CoreModel


class CrawlOptions(CoreModel):
    allowed_hosts: list[str] = Field(default_factory=list)
    max_pages: int = Field(default=25, ge=1)
    max_depth: int = Field(default=2, ge=0)
    include_patterns: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)


class CrawlPage(CoreModel):
    url: str
    normalized_url: str
    final_url: str
    status_code: int
    depth: int
    discovered_from: str | None = None
    content_type: str | None = None
    error: str | None = None
    links_found: int = 0
    main_content: MainContent | None = None


class MainContent(CoreModel):
    selector: str | None = None
    text: str = ""
    text_length: int = Field(default=0, ge=0)
    word_count: int = Field(default=0, ge=0)


class DiscoveredLink(CoreModel):
    raw_href: str
    resolved_url: str
    normalized_url: str
    anchor_text: str | None = None
    source_url: str
    depth: int


class SkippedUrl(CoreModel):
    url: str
    reason: str
    source_url: str | None = None


class CrawlResult(CoreModel):
    start_url: str
    pages: list[CrawlPage] = Field(default_factory=list)
    discovered_urls: list[DiscoveredLink] = Field(default_factory=list)
    skipped_urls: list[SkippedUrl] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    max_pages_reached: bool = False
