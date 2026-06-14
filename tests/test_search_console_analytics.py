import json

import pytest

from geo_seo_engine.search_console import load_search_console_analytics, parse_search_console_rows


def test_parse_search_console_rows_validates_and_normalizes_rows():
    result = parse_search_console_rows(
        [
            {
                "query": "seo audit",
                "page": "HTTPS://Example.com/Guide#intro",
                "date": "2026-01-15",
                "country": "br",
                "device": "DESKTOP",
                "clicks": "4",
                "impressions": "20",
                "ctr": "20%",
                "position": "3.5",
            }
        ]
    )

    assert result.invalid_rows == []
    assert result.rows[0].normalized_page == "https://example.com/Guide"
    assert result.rows[0].country == "BR"
    assert result.rows[0].device == "desktop"
    assert result.rows[0].ctr == 0.2


def test_parse_search_console_rows_collects_invalid_rows():
    result = parse_search_console_rows(
        [
            {
                "query": "seo audit",
                "page": "not-a-url",
                "date": "15/01/2026",
                "country": "BR",
                "device": "mobile",
                "clicks": "8",
                "impressions": "5",
                "ctr": "1.2",
                "position": "-1",
            }
        ]
    )

    assert result.rows == []
    assert {error.field for error in result.invalid_rows} == {"page", "date", "clicks", "ctr", "position"}


def test_parse_search_console_rows_aggregates_by_dimensions():
    result = parse_search_console_rows(
        [
            _row(page="https://example.com/a", query="alpha", clicks=2, impressions=10, position=2.0),
            _row(page="https://example.com/a", query="beta", clicks=1, impressions=30, position=4.0),
            _row(page="https://example.com/b", query="alpha", clicks=3, impressions=10, position=8.0, device="desktop"),
        ]
    )

    assert result.aggregate.clicks == 6
    assert result.aggregate.impressions == 50
    assert result.aggregate.ctr == 0.12
    assert result.aggregate.position == pytest.approx(4.4)
    assert result.groups.by_page[0].key == "https://example.com/a"
    assert result.groups.by_page[0].clicks == 3
    assert result.groups.by_query[0].key == "alpha"
    assert result.groups.by_device[0].key == "mobile"
    assert result.groups.by_country[0].key == "BR"
    assert result.groups.by_date[0].key == "2026-01-15"


def test_load_search_console_analytics_reads_json_rows(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps({"rows": [_api_row()]}), encoding="utf-8")

    result = load_search_console_analytics(input_path)

    assert result.rows[0].query == "geo seo"
    assert result.rows[0].normalized_page == "https://example.com/page"
    assert result.aggregate.clicks == 5


def test_load_search_console_analytics_reads_csv_rows(tmp_path):
    input_path = tmp_path / "input.csv"
    input_path.write_text(
        "query,page,date,country,device,clicks,impressions,ctr,position\n"
        "geo seo,https://example.com/page,2026-01-15,BR,mobile,5,25,0.2,2.5\n",
        encoding="utf-8",
    )

    result = load_search_console_analytics(input_path)

    assert result.rows[0].query == "geo seo"
    assert result.aggregate.ctr == 0.2


def test_load_search_console_analytics_accepts_title_case_csv_headers(tmp_path):
    input_path = tmp_path / "input.csv"
    input_path.write_text(
        "Query,Page,Date,Country,Device,Clicks,Impressions,CTR,Position\n"
        "geo seo,https://example.com/page,2026-01-15,BR,mobile,5,25,20%,2.5\n",
        encoding="utf-8",
    )

    result = load_search_console_analytics(input_path)

    assert result.invalid_rows == []
    assert result.rows[0].query == "geo seo"
    assert result.rows[0].normalized_page == "https://example.com/page"
    assert result.rows[0].ctr == 0.2
    assert result.aggregate.position == 2.5


def _row(
    page: str,
    query: str,
    clicks: int,
    impressions: int,
    position: float,
    device: str = "mobile",
):
    return {
        "query": query,
        "page": page,
        "date": "2026-01-15",
        "country": "BR",
        "device": device,
        "clicks": clicks,
        "impressions": impressions,
        "ctr": clicks / impressions,
        "position": position,
    }


def _api_row():
    return {
        "keys": ["geo seo", "https://example.com/page", "2026-01-15", "BR", "mobile"],
        "clicks": 5,
        "impressions": 25,
        "ctr": 0.2,
        "position": 2.5,
    }
