from __future__ import annotations

from typing import Protocol

from geo_seo_engine.rendering.models import RenderedPage


class PageRenderer(Protocol):
    def render(self, url: str, html: str | None = None) -> RenderedPage: ...


class StaticHtmlRenderer:
    """Test/local renderer that treats crawl-time HTML as rendered output."""

    def render(self, url: str, html: str | None = None) -> RenderedPage:
        return RenderedPage(page_url=url, html=html or "", status="rendered")


class UnavailableRenderer:
    def render(self, url: str, html: str | None = None) -> RenderedPage:
        del html
        return RenderedPage(
            page_url=url,
            html=None,
            status="skipped",
            error="No JavaScript renderer is configured. Pass --renderer static for static test mode or integrate a PageRenderer implementation.",
        )
