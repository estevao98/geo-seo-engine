from __future__ import annotations

from typing import Protocol

from geo_seo_engine.performance.models import PagePerformanceSnapshot


class PerformanceDataProvider(Protocol):
    def fetch(self, url: str, strategy: str = "mobile") -> PagePerformanceSnapshot: ...
