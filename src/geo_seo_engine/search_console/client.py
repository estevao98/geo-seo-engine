from __future__ import annotations

from datetime import date
from typing import Protocol


class SearchConsoleDataProvider(Protocol):
    """Boundary for future Search Console API clients.

    Implementations can fetch API rows, while tests and default CLI usage keep
    using local JSON/CSV files without credentials.
    """

    def fetch_search_analytics(
        self,
        site_url: str,
        start_date: date,
        end_date: date,
        dimensions: list[str],
    ) -> list[dict]: ...
