from __future__ import annotations

from typing import Any

from geo_seo_engine.performance.models import (
    PagePerformanceSnapshot,
    PerformanceMetric,
    PerformanceOpportunity,
)


METRIC_AUDIT_IDS = {
    "first-contentful-paint": ("First Contentful Paint", "ms"),
    "largest-contentful-paint": ("Largest Contentful Paint", "ms"),
    "cumulative-layout-shift": ("Cumulative Layout Shift", "score"),
    "total-blocking-time": ("Total Blocking Time", "ms"),
    "speed-index": ("Speed Index", "ms"),
    "interaction-to-next-paint": ("Interaction to Next Paint", "ms"),
    "server-response-time": ("Time To First Byte", "ms"),
    "experimental-time-to-first-byte": ("Time To First Byte", "ms"),
}

FIELD_METRIC_IDS = {
    "FIRST_CONTENTFUL_PAINT_MS": ("first-contentful-paint", "First Contentful Paint", "ms"),
    "LARGEST_CONTENTFUL_PAINT_MS": ("largest-contentful-paint", "Largest Contentful Paint", "ms"),
    "CUMULATIVE_LAYOUT_SHIFT_SCORE": ("cumulative-layout-shift", "Cumulative Layout Shift", "score"),
    "INTERACTION_TO_NEXT_PAINT": ("interaction-to-next-paint", "Interaction to Next Paint", "ms"),
    "EXPERIMENTAL_TIME_TO_FIRST_BYTE": ("experimental-time-to-first-byte", "Time To First Byte", "ms"),
}


def parse_pagespeed_result(
    payload: dict[str, Any],
    page_url: str | None = None,
) -> PagePerformanceSnapshot:
    lighthouse = _as_dict(payload.get("lighthouseResult"))
    config_settings = _as_dict(lighthouse.get("configSettings"))
    audits = _as_dict(lighthouse.get("audits"))
    categories = _as_dict(lighthouse.get("categories"))
    performance_category = _as_dict(categories.get("performance"))

    requested_url = _string_or_none(payload.get("id")) or _string_or_none(lighthouse.get("requestedUrl"))
    final_url = _string_or_none(lighthouse.get("finalUrl")) or _string_or_none(payload.get("finalUrl"))
    effective_page_url = page_url or final_url or requested_url or "unknown"

    lab_metrics = _parse_lab_metrics(audits)
    field_metrics = _parse_field_metrics(payload)
    metrics = lab_metrics + field_metrics

    return PagePerformanceSnapshot(
        page_url=effective_page_url,
        requested_url=requested_url,
        final_url=final_url,
        strategy=_string_or_none(config_settings.get("formFactor")) or _string_or_none(payload.get("strategy")) or "mobile",
        source=_string_or_none(payload.get("source")) or "pagespeed",
        performance_score=_parse_score(performance_category.get("score")),
        metrics=metrics,
        opportunities=_parse_audit_group(audits, group="opportunity"),
        diagnostics=_parse_audit_group(audits, group="diagnostic"),
        has_lab_data=bool(lab_metrics or performance_category),
        has_field_data=bool(field_metrics),
        raw_source_version=_string_or_none(lighthouse.get("lighthouseVersion")),
    )


def _parse_lab_metrics(audits: dict[str, Any]) -> list[PerformanceMetric]:
    metrics: list[PerformanceMetric] = []
    for audit_id, (fallback_label, fallback_unit) in METRIC_AUDIT_IDS.items():
        audit = _as_dict(audits.get(audit_id))
        if not audit:
            continue
        metrics.append(
            PerformanceMetric(
                id=audit_id,
                label=_string_or_none(audit.get("title")) or fallback_label,
                value=_number_or_none(audit.get("numericValue")),
                unit=_string_or_none(audit.get("numericUnit")) or fallback_unit,
                display_value=_string_or_none(audit.get("displayValue")),
                category="lab",
                source="lighthouse",
            )
        )
    return metrics


def _parse_field_metrics(payload: dict[str, Any]) -> list[PerformanceMetric]:
    metrics: list[PerformanceMetric] = []
    for source_key, source_label in (
        ("loadingExperience", "page"),
        ("originLoadingExperience", "origin"),
    ):
        source_payload = _as_dict(payload.get(source_key))
        source_metrics = _as_dict(source_payload.get("metrics"))
        for raw_id, (metric_id, label, unit) in FIELD_METRIC_IDS.items():
            metric = _as_dict(source_metrics.get(raw_id))
            percentile = _number_or_none(metric.get("percentile"))
            if percentile is None:
                continue
            metrics.append(
                PerformanceMetric(
                    id=metric_id,
                    label=label,
                    value=percentile,
                    unit=unit,
                    display_value=_field_display_value(percentile, unit),
                    category="field",
                    source=f"crux_{source_label}",
                )
            )
    return metrics


def _parse_audit_group(audits: dict[str, Any], group: str) -> list[PerformanceOpportunity]:
    items: list[PerformanceOpportunity] = []
    for audit_id, raw_audit in audits.items():
        audit = _as_dict(raw_audit)
        details = _as_dict(audit.get("details"))
        details_type = _string_or_none(details.get("type"))
        score_mode = _string_or_none(audit.get("scoreDisplayMode"))
        is_opportunity = details_type == "opportunity" or score_mode == "opportunity"
        is_diagnostic = details_type == "diagnostic"
        if (group == "opportunity" and not is_opportunity) or (group == "diagnostic" and not is_diagnostic):
            continue

        items.append(
            PerformanceOpportunity(
                id=str(audit_id),
                title=_string_or_none(audit.get("title")) or str(audit_id),
                description=_string_or_none(audit.get("description")),
                score=_score_or_none(audit.get("score")),
                estimated_savings_ms=_number_or_none(details.get("overallSavingsMs")),
                estimated_savings_bytes=_number_or_none(details.get("overallSavingsBytes")),
            )
        )
    return items


def _parse_score(raw_score: Any) -> float | None:
    score = _number_or_none(raw_score)
    if score is None:
        return None
    return score * 100 if score <= 1 else score


def _score_or_none(raw_score: Any) -> float | None:
    score = _number_or_none(raw_score)
    if score is None or score < 0 or score > 1:
        return None
    return score


def _field_display_value(value: float, unit: str) -> str:
    if unit == "score":
        return str(value)
    return f"{value:g} ms"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _number_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None
