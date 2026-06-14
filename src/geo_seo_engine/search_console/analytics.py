from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from pydantic import ValidationError

from geo_seo_engine.core.url import normalize_url
from geo_seo_engine.search_console.models import (
    SearchConsoleAnalyticsResult,
    SearchConsoleGroupedSummaries,
    SearchConsoleGroupSummary,
    SearchConsoleMetricSummary,
    SearchConsoleRow,
    SearchConsoleValidationError,
)

DEFAULT_DIMENSIONS = ("query", "page", "date", "country", "device")
REQUIRED_FIELDS = (*DEFAULT_DIMENSIONS, "clicks", "impressions", "ctr", "position")


def load_search_console_analytics(path: Path | str) -> SearchConsoleAnalyticsResult:
    input_path = Path(path)
    suffix = input_path.suffix.lower()
    if suffix == ".json":
        records = _load_json_records(input_path)
    elif suffix == ".csv":
        records = _load_csv_records(input_path)
    else:
        raise ValueError("Search Console input must be a .json or .csv file.")

    return parse_search_console_rows(records, source=str(input_path))


def parse_search_console_rows(records: Iterable[dict[str, Any]], source: str | None = None) -> SearchConsoleAnalyticsResult:
    rows: list[SearchConsoleRow] = []
    invalid_rows: list[SearchConsoleValidationError] = []

    for row_number, record in enumerate(records, start=1):
        row, errors = _parse_record(record, row_number)
        if errors:
            invalid_rows.extend(errors)
            continue
        rows.append(row)

    return SearchConsoleAnalyticsResult(
        source=source,
        rows=rows,
        invalid_rows=invalid_rows,
        aggregate=_summarize(rows),
        groups=SearchConsoleGroupedSummaries(
            by_page=_group(rows, lambda row: row.normalized_page),
            by_query=_group(rows, lambda row: row.query),
            by_device=_group(rows, lambda row: row.device),
            by_country=_group(rows, lambda row: row.country),
            by_date=_group(rows, lambda row: row.date.isoformat()),
        ),
    )


def _load_json_records(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Could not read Search Console JSON: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid Search Console JSON: {exc}") from exc

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        records = payload["rows"]
    else:
        raise ValueError("Search Console JSON must be a list or an object with a rows list.")

    if not all(isinstance(record, dict) for record in records):
        raise ValueError("Each Search Console JSON row must be an object.")
    return records


def _load_csv_records(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            return list(csv.DictReader(csv_file))
    except OSError as exc:
        raise ValueError(f"Could not read Search Console CSV: {exc}") from exc


def _parse_record(record: dict[str, Any], row_number: int) -> tuple[SearchConsoleRow | None, list[SearchConsoleValidationError]]:
    normalized_record = _expand_api_keys(record)
    errors: list[SearchConsoleValidationError] = []
    values: dict[str, Any] = {}

    for field in REQUIRED_FIELDS:
        raw_value = _get_field(normalized_record, field)
        if raw_value is None or (isinstance(raw_value, str) and not raw_value.strip()):
            errors.append(_error(row_number, field, "required field is missing or empty", raw_value))
            continue
        values[field] = raw_value

    if errors:
        return None, errors

    query = str(values["query"]).strip()
    page = str(values["page"]).strip()
    country = str(values["country"]).strip().upper()
    device = str(values["device"]).strip().lower()

    try:
        normalized_page = normalize_url(page).normalized_url
    except ValueError as exc:
        errors.append(_error(row_number, "page", str(exc), page))
        normalized_page = page

    parsed_date = _parse_date(values["date"], row_number, errors)
    clicks = _parse_int(values["clicks"], "clicks", row_number, errors)
    impressions = _parse_int(values["impressions"], "impressions", row_number, errors)
    ctr = _parse_ctr(values["ctr"], row_number, errors)
    position = _parse_float(values["position"], "position", row_number, errors)

    if clicks is not None and impressions is not None and clicks > impressions:
        errors.append(_error(row_number, "clicks", "clicks cannot exceed impressions", clicks))

    if errors or parsed_date is None or clicks is None or impressions is None or ctr is None or position is None:
        return None, errors

    try:
        return (
            SearchConsoleRow(
                query=query,
                page=page,
                normalized_page=normalized_page,
                date=parsed_date,
                country=country,
                device=device,
                clicks=clicks,
                impressions=impressions,
                ctr=ctr,
                position=position,
            ),
            [],
        )
    except ValidationError as exc:
        for line_error in exc.errors():
            field = ".".join(str(part) for part in line_error["loc"])
            errors.append(_error(row_number, field, str(line_error["msg"]), values.get(field)))
        return None, errors


def _expand_api_keys(record: dict[str, Any]) -> dict[str, Any]:
    expanded = dict(record)
    keys = expanded.get("keys")
    if isinstance(keys, list):
        for field, value in zip(DEFAULT_DIMENSIONS, keys, strict=False):
            expanded.setdefault(field, value)
    return expanded


def _get_field(record: dict[str, Any], field: str) -> Any:
    aliases = {
        "page": ("page", "url"),
        "ctr": ("ctr", "CTR"),
        "position": ("position", "average_position", "Average position"),
    }
    for key in aliases.get(field, (field, field.title())):
        if key in record:
            return record[key]
    return None


def _parse_date(value: Any, row_number: int, errors: list[SearchConsoleValidationError]) -> date | None:
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        errors.append(_error(row_number, "date", "date must use ISO format YYYY-MM-DD", value))
        return None


def _parse_int(value: Any, field: str, row_number: int, errors: list[SearchConsoleValidationError]) -> int | None:
    try:
        parsed = int(str(value).strip())
    except ValueError:
        errors.append(_error(row_number, field, "must be an integer", value))
        return None
    if parsed < 0:
        errors.append(_error(row_number, field, "must be greater than or equal to 0", value))
        return None
    return parsed


def _parse_ctr(value: Any, row_number: int, errors: list[SearchConsoleValidationError]) -> float | None:
    raw_value = str(value).strip()
    try:
        parsed = float(raw_value.rstrip("%"))
    except ValueError:
        errors.append(_error(row_number, "ctr", "must be a number between 0 and 1", value))
        return None
    if raw_value.endswith("%"):
        parsed = parsed / 100
    if parsed < 0 or parsed > 1:
        errors.append(_error(row_number, "ctr", "must be between 0 and 1", value))
        return None
    return parsed


def _parse_float(value: Any, field: str, row_number: int, errors: list[SearchConsoleValidationError]) -> float | None:
    try:
        parsed = float(str(value).strip())
    except ValueError:
        errors.append(_error(row_number, field, "must be a number", value))
        return None
    if parsed < 0:
        errors.append(_error(row_number, field, "must be greater than or equal to 0", value))
        return None
    return parsed


def _summarize(rows: list[SearchConsoleRow]) -> SearchConsoleMetricSummary:
    clicks = sum(row.clicks for row in rows)
    impressions = sum(row.impressions for row in rows)
    return SearchConsoleMetricSummary(
        rows=len(rows),
        clicks=clicks,
        impressions=impressions,
        ctr=clicks / impressions if impressions else 0.0,
        position=_weighted_position(rows),
    )


def _group(rows: list[SearchConsoleRow], key_for_row) -> list[SearchConsoleGroupSummary]:
    grouped: dict[str, list[SearchConsoleRow]] = defaultdict(list)
    for row in rows:
        grouped[key_for_row(row)].append(row)

    summaries = [SearchConsoleGroupSummary(key=key, **_summarize(group_rows).model_dump()) for key, group_rows in grouped.items()]
    return sorted(summaries, key=lambda summary: (-summary.clicks, -summary.impressions, summary.key))


def _weighted_position(rows: list[SearchConsoleRow]) -> float:
    impressions = sum(row.impressions for row in rows)
    if not impressions:
        return 0.0
    return sum(row.position * row.impressions for row in rows) / impressions


def _error(row_number: int, field: str, message: str, value: Any) -> SearchConsoleValidationError:
    return SearchConsoleValidationError(row_number=row_number, field=field, message=message, value=value)
