from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from pydantic import ValidationError

from geo_seo_engine.core.models import Evidence
from geo_seo_engine.core.url import normalize_url
from geo_seo_engine.opportunities.models import (
    Opportunity,
    OpportunityAnalyticsSignal,
    OpportunityBucket,
    OpportunityEngineResult,
    OpportunityScoreComponents,
    OpportunitySummary,
)

AUDIT_INPUTS = (
    "technical",
    "content_quality",
    "entity_readiness",
    "internal_links",
    "performance",
)

FINDING_KEYS_BY_INPUT = {
    "technical": ("technical", "technical_audit", "audit_technical"),
    "content_quality": ("content_quality", "content", "audit_content_quality"),
    "entity_readiness": ("entity_readiness", "entity", "audit_entity_readiness"),
    "internal_links": ("internal_links", "internal_link_graph", "audit_internal_links"),
    "performance": ("performance", "audit_performance"),
}

SEARCH_CONSOLE_KEYS = ("search_console", "search_console_analytics", "gsc")

SEVERITY_POINTS = {
    "critical": 40.0,
    "high": 32.0,
    "medium": 22.0,
    "low": 12.0,
    "info": 6.0,
}
IMPACT_POINTS = {"high": 24.0, "medium": 16.0, "low": 8.0, "unknown": 10.0}
EFFORT_POINTS = {"low": 16.0, "medium": 10.0, "high": 5.0, "unknown": 8.0}


def run_opportunity_engine(payload: dict[str, Any]) -> OpportunityEngineResult:
    """Build deterministic opportunities from local audit JSON outputs."""
    analytics_by_page = _extract_search_console_pages(payload)
    opportunities = []
    inputs_present: list[str] = []
    inputs_missing: list[str] = []

    for source in AUDIT_INPUTS:
        findings = _extract_findings(payload, source)
        if _input_present(payload, source):
            inputs_present.append(source)
        else:
            inputs_missing.append(source)

        for index, finding in enumerate(findings, start=1):
            opportunities.append(_build_opportunity(source, finding, index, analytics_by_page))

    opportunities.sort(key=lambda item: (-item.score, item.page_url or "", item.type, item.id))

    return OpportunityEngineResult(
        opportunities=opportunities,
        buckets_by_page=_build_buckets(opportunities, "page"),
        buckets_by_type=_build_buckets(opportunities, "type"),
        buckets_by_priority=_build_buckets(opportunities, "priority"),
        summary=_build_summary(opportunities, inputs_present, inputs_missing, bool(analytics_by_page)),
    )


def _extract_findings(payload: dict[str, Any], source: str) -> list[dict[str, Any]]:
    for key in FINDING_KEYS_BY_INPUT[source]:
        value = payload.get(key)
        if isinstance(value, dict):
            findings = value.get("findings")
            if isinstance(findings, list):
                return [finding for finding in findings if isinstance(finding, dict)]
        if isinstance(value, list):
            return [finding for finding in value if isinstance(finding, dict)]

    if source == "technical" and isinstance(payload.get("findings"), list):
        return [finding for finding in payload["findings"] if isinstance(finding, dict)]
    return []


def _input_present(payload: dict[str, Any], source: str) -> bool:
    if source == "technical" and isinstance(payload.get("findings"), list):
        return True
    return any(key in payload for key in FINDING_KEYS_BY_INPUT[source])


def _build_opportunity(
    source: str,
    finding: dict[str, Any],
    index: int,
    analytics_by_page: dict[str, OpportunityAnalyticsSignal],
) -> Opportunity:
    finding_id = str(finding.get("id") or f"{source}.finding_{index}")
    page_url = _page_url(finding)
    severity = _normalized_signal(finding.get("severity"), SEVERITY_POINTS, "medium")
    impact = _extract_signal(finding, "impact", _default_impact_for_severity(severity), IMPACT_POINTS)
    effort = _extract_signal(finding, "effort", "unknown", EFFORT_POINTS)
    confidence = _bounded_float(finding.get("confidence"), default=1.0, minimum=0.0, maximum=1.0)
    analytics = analytics_by_page.get(page_url or "")
    components = _score_components(severity, impact, effort, confidence, analytics)
    priority = _priority(components.total)
    type_name = _type_name(source, finding)

    return Opportunity(
        id=_opportunity_id(source, finding_id, page_url, index),
        finding_id=finding_id,
        source=source,
        type=type_name,
        page_url=page_url,
        title=str(finding.get("title") or finding_id),
        severity=severity,
        impact=impact,
        effort=effort,
        confidence=confidence,
        priority=priority,
        score=components.total,
        score_components=components,
        rationale=_rationale(severity, impact, effort, confidence, analytics),
        evidence=_evidence(finding.get("evidence")),
        risk=_string_or_none(finding.get("risk")),
        next_action=_next_action(finding),
        analytics=analytics,
    )


def _score_components(
    severity: str,
    impact: str,
    effort: str,
    confidence: float,
    analytics: OpportunityAnalyticsSignal | None,
) -> OpportunityScoreComponents:
    severity_score = SEVERITY_POINTS[severity]
    impact_score = IMPACT_POINTS[impact]
    effort_score = EFFORT_POINTS[effort]
    confidence_score = round(confidence * 14.0, 2)
    analytics_score = _analytics_score(analytics)
    total = min(100.0, severity_score + impact_score + effort_score + confidence_score + analytics_score)
    return OpportunityScoreComponents(
        severity=severity_score,
        impact=impact_score,
        effort=effort_score,
        confidence=confidence_score,
        analytics=analytics_score,
        total=round(total, 2),
    )


def _analytics_score(analytics: OpportunityAnalyticsSignal | None) -> float:
    if analytics is None or analytics.impressions <= 0:
        return 0.0
    impression_score = min(6.0, analytics.impressions / 1000.0 * 6.0)
    position_score = 4.0 if analytics.position >= 8.0 else 2.0 if analytics.position >= 4.0 else 0.0
    ctr_score = 2.0 if analytics.ctr <= 0.02 else 1.0 if analytics.ctr <= 0.05 else 0.0
    return round(impression_score + position_score + ctr_score, 2)


def _extract_search_console_pages(payload: dict[str, Any]) -> dict[str, OpportunityAnalyticsSignal]:
    search_console = None
    for key in SEARCH_CONSOLE_KEYS:
        if isinstance(payload.get(key), dict):
            search_console = payload[key]
            break
    if not search_console:
        return {}

    groups = search_console.get("groups")
    by_page = groups.get("by_page") if isinstance(groups, dict) else search_console.get("by_page")
    if not isinstance(by_page, list):
        return {}

    signals = {}
    for item in by_page:
        if not isinstance(item, dict):
            continue
        page = _normalize_page_key(_string_or_none(item.get("key") or item.get("page") or item.get("normalized_page")))
        if not page:
            continue
        signals[page] = OpportunityAnalyticsSignal(
            impressions=max(0, _int_or_zero(item.get("impressions"))),
            clicks=max(0, _int_or_zero(item.get("clicks"))),
            ctr=_bounded_float(item.get("ctr"), default=0.0, minimum=0.0, maximum=1.0),
            position=max(0.0, _bounded_float(item.get("position"), default=0.0, minimum=0.0, maximum=1_000_000.0)),
        )
    return signals


def _build_buckets(opportunities: list[Opportunity], group_by: str) -> list[OpportunityBucket]:
    grouped: dict[str, list[Opportunity]] = defaultdict(list)
    for opportunity in opportunities:
        if group_by == "page":
            key = opportunity.page_url or "sitewide"
        elif group_by == "type":
            key = opportunity.type
        else:
            key = opportunity.priority
        grouped[key].append(opportunity)

    buckets = []
    for key, items in grouped.items():
        scores = [item.score for item in items]
        buckets.append(
            OpportunityBucket(
                group_by=group_by,
                key=key,
                count=len(items),
                max_score=round(max(scores), 2),
                average_score=round(sum(scores) / len(scores), 2),
                opportunity_ids=[item.id for item in items],
            )
        )
    return sorted(buckets, key=lambda bucket: (-bucket.max_score, bucket.key))


def _build_summary(
    opportunities: list[Opportunity],
    inputs_present: list[str],
    inputs_missing: list[str],
    has_search_console: bool,
) -> OpportunitySummary:
    by_priority = Counter(item.priority for item in opportunities)
    by_type = Counter(item.type for item in opportunities)
    by_page = Counter(item.page_url or "sitewide" for item in opportunities)
    present = list(inputs_present)
    missing = list(inputs_missing)
    if has_search_console:
        present.append("search_console")
    else:
        missing.append("search_console")

    return OpportunitySummary(
        total_opportunities=len(opportunities),
        by_priority=dict(sorted(by_priority.items())),
        by_type=dict(sorted(by_type.items())),
        by_page=dict(sorted(by_page.items())),
        top_opportunity_ids=[item.id for item in opportunities[:10]],
        inputs_present=present,
        inputs_missing=missing,
    )


def _page_url(finding: dict[str, Any]) -> str | None:
    return _normalize_page_key(_string_or_none(finding.get("page_url") or finding.get("url") or finding.get("normalized_url")))


def _type_name(source: str, finding: dict[str, Any]) -> str:
    category = _string_or_none(finding.get("category"))
    if category:
        return category
    finding_id = _string_or_none(finding.get("id"))
    if finding_id and "." in finding_id:
        return finding_id.split(".", 1)[0]
    return source


def _extract_signal(finding: dict[str, Any], key: str, default: str, allowed: dict[str, float]) -> str:
    direct = _normalized_signal(finding.get(key), allowed, "")
    if direct:
        return direct
    recommendation = finding.get("recommendation")
    if isinstance(recommendation, dict):
        nested = _normalized_signal(recommendation.get(key), allowed, "")
        if nested:
            return nested
    return default


def _normalized_signal(value: Any, allowed: dict[str, float], default: str) -> str:
    if value is None:
        return default
    candidate = str(value).strip().lower()
    return candidate if candidate in allowed else default


def _default_impact_for_severity(severity: str) -> str:
    if severity in {"critical", "high"}:
        return "high"
    if severity == "medium":
        return "medium"
    return "low"


def _priority(score: float) -> str:
    if score >= 80.0:
        return "critical"
    if score >= 65.0:
        return "high"
    if score >= 45.0:
        return "medium"
    return "low"


def _rationale(
    severity: str,
    impact: str,
    effort: str,
    confidence: float,
    analytics: OpportunityAnalyticsSignal | None,
) -> list[str]:
    reasons = [
        f"Severity signal is {severity}.",
        f"Impact signal is {impact}.",
        f"Effort signal is {effort}; lower effort raises priority.",
        f"Confidence signal is {confidence:.2f}.",
    ]
    if analytics is not None:
        reasons.append(
            "Search Console summary is used only as observed demand/context: "
            f"{analytics.impressions} impressions, {analytics.clicks} clicks, "
            f"CTR {analytics.ctr:.2%}, average position {analytics.position:.2f}."
        )
    else:
        reasons.append("No Search Console page summary was available; analytics score is 0.")
    return reasons


def _evidence(raw_evidence: Any) -> list[Evidence]:
    if not isinstance(raw_evidence, list):
        return []
    evidence = []
    for item in raw_evidence:
        if not isinstance(item, dict):
            continue
        try:
            evidence.append(Evidence.model_validate(item))
        except ValidationError:
            continue
    return evidence


def _next_action(finding: dict[str, Any]) -> str:
    direct = _string_or_none(finding.get("next_action"))
    if direct:
        return direct
    recommendation = finding.get("recommendation")
    if isinstance(recommendation, dict):
        action = _string_or_none(recommendation.get("action"))
        if action:
            return action
    if isinstance(recommendation, str) and recommendation.strip():
        return recommendation.strip()
    return "Review the finding evidence and define the smallest safe remediation."


def _opportunity_id(source: str, finding_id: str, page_url: str | None, index: int) -> str:
    page_part = _slug(page_url or "sitewide")[:40]
    return f"opportunity.{source}.{_slug(finding_id)}.{page_part}.{index}"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def _normalize_page_key(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return normalize_url(value).normalized_url
    except ValueError:
        return value


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bounded_float(value: Any, *, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, minimum), maximum)


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
