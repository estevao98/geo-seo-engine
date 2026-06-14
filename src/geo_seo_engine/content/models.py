from __future__ import annotations

from pydantic import Field

from geo_seo_engine.core.models import CoreModel


class ContentHeading(CoreModel):
    level: int = Field(ge=1, le=6)
    text: str
    order: int = Field(ge=0)


class ContentTextBlock(CoreModel):
    text: str
    tag: str
    word_count: int = Field(default=0, ge=0)
    order: int = Field(ge=0)


class ContentLink(CoreModel):
    url: str
    anchor_text: str | None = None
    is_internal: bool


class ExtractedMainContent(CoreModel):
    page_url: str
    title: str | None = None
    meta_description: str | None = None
    canonical_url: str | None = None
    extraction_method: str
    main_selector: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    headings: list[ContentHeading] = Field(default_factory=list)
    text_blocks: list[ContentTextBlock] = Field(default_factory=list)
    links: list[ContentLink] = Field(default_factory=list)
    image_alt_texts: list[str] = Field(default_factory=list)
    plain_text: str = ""
    word_count: int = Field(default=0, ge=0)
    character_count: int = Field(default=0, ge=0)
    paragraph_count: int = Field(default=0, ge=0)
    heading_count: int = Field(default=0, ge=0)
    link_count: int = Field(default=0, ge=0)
    internal_link_count: int = Field(default=0, ge=0)
    external_link_count: int = Field(default=0, ge=0)
    image_count: int = Field(default=0, ge=0)
    images_missing_alt_count: int = Field(default=0, ge=0)
    boilerplate_removed: bool = False


class ContentExtractionSummary(CoreModel):
    total_pages: int = Field(default=0, ge=0)
    pages_with_main_content: int = Field(default=0, ge=0)
    pages_missing_main_content: int = Field(default=0, ge=0)
    average_word_count: float = Field(default=0.0, ge=0.0)
    low_word_count_pages: list[str] = Field(default_factory=list)
    extraction_methods: dict[str, int] = Field(default_factory=dict)


class ContentExtractionResult(CoreModel):
    start_url: str | None = None
    pages: list[ExtractedMainContent] = Field(default_factory=list)
    summary: ContentExtractionSummary
