from __future__ import annotations

from datetime import date

from pydantic import Field

from geo_seo_engine.core.models import CoreModel


class SearchConsoleRow(CoreModel):
    query: str
    page: str
    normalized_page: str
    date: date
    country: str
    device: str
    clicks: int = Field(ge=0)
    impressions: int = Field(ge=0)
    ctr: float = Field(ge=0.0, le=1.0)
    position: float = Field(ge=0.0)


class SearchConsoleValidationError(CoreModel):
    row_number: int
    field: str
    message: str
    value: str | int | float | bool | None = None


class SearchConsoleMetricSummary(CoreModel):
    rows: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    impressions: int = Field(default=0, ge=0)
    ctr: float = Field(default=0.0, ge=0.0)
    position: float = Field(default=0.0, ge=0.0)


class SearchConsoleGroupSummary(SearchConsoleMetricSummary):
    key: str


class SearchConsoleGroupedSummaries(CoreModel):
    by_page: list[SearchConsoleGroupSummary] = Field(default_factory=list)
    by_query: list[SearchConsoleGroupSummary] = Field(default_factory=list)
    by_device: list[SearchConsoleGroupSummary] = Field(default_factory=list)
    by_country: list[SearchConsoleGroupSummary] = Field(default_factory=list)
    by_date: list[SearchConsoleGroupSummary] = Field(default_factory=list)


class SearchConsoleAnalyticsResult(CoreModel):
    source: str | None = None
    rows: list[SearchConsoleRow] = Field(default_factory=list)
    invalid_rows: list[SearchConsoleValidationError] = Field(default_factory=list)
    aggregate: SearchConsoleMetricSummary
    groups: SearchConsoleGroupedSummaries
