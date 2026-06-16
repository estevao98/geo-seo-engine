from __future__ import annotations

from collections import Counter
from typing import Any

from pydantic import ValidationError

from geo_seo_engine.core.models import Evidence
from geo_seo_engine.senior_report.models import (
    SeniorAIReadinessSummary,
    SeniorClusterContentSummary,
    SeniorEvidenceReference,
    SeniorHealthSnapshot,
    SeniorOperationalAction,
    SeniorOpportunitySummary,
    SeniorPriorityRisk,
    SeniorReportCoverageItem,
    SeniorReportResult,
    SeniorReportSummary,
)


EXPECTED_INPUTS = (
    "technical",
    "content_quality",
    "entity_readiness",
    "main_content",
    "internal_links",
    "search_console",
    "opportunities",
    "content_briefs",
    "content_clusters",
    "ai_readiness",
)

INPUT_ALIASES = {
    "technical": ("technical", "technical_audit", "audit_technical"),
    "content_quality": ("content_quality", "audit_content_quality"),
    "entity_readiness": ("entity_readiness", "audit_entity_readiness"),
    "main_content": ("main_content", "content_extraction", "content"),
    "internal_links": ("internal_links", "internal_link_graph", "audit_internal_links"),
    "search_console": ("search_console", "search_console_analytics", "gsc"),
    "opportunities": ("opportunities", "opportunity", "opportunity_engine"),
    "content_briefs": ("content_briefs", "briefs", "content_brief"),
    "content_clusters": ("content_clusters", "clusters", "content_cluster"),
    "ai_readiness": ("ai_readiness", "ai_readiness_simulation", "readiness"),
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def generate_senior_report(payload: dict[str, Any]) -> SeniorReportResult:
    """Generate a deterministic senior executive and operational report from local JSON."""
    inputs = {name: _input_value(payload, name) for name in EXPECTED_INPUTS}
    coverage = [_coverage_item(name, inputs[name]) for name in EXPECTED_INPUTS]
    available_inputs = [item.input_name for item in coverage if item.present]
    missing_inputs = [item.input_name for item in coverage if not item.present]

    findings = _all_findings(inputs)
    opportunities = _items(inputs["opportunities"], "opportunities")
    briefs = _items(inputs["content_briefs"], "briefs")
    clusters = _items(inputs["content_clusters"], "clusters")
    ai_findings = _items(inputs["ai_readiness"], "findings")
    actions = _operational_actions(findings, opportunities, briefs, ai_findings)
    risks = _top_risks(findings, opportunities, ai_findings)
    evidence_refs = _evidence_references(findings, opportunities, briefs, clusters, ai_findings)
    limitations = _limitations(coverage, inputs, ai_findings, clusters, briefs)

    return SeniorReportResult(
        executive_summary=_executive_summary(available_inputs, missing_inputs, findings, opportunities, actions),
        health_readiness_snapshot=_health_snapshot(inputs, findings, opportunities, briefs, clusters, ai_findings),
        top_risks_and_priorities=risks,
        input_coverage=coverage,
        opportunity_and_remediation_summary=_opportunity_summary(opportunities),
        ai_geo_readiness_summary=_ai_geo_summary(inputs["ai_readiness"], ai_findings),
        cluster_and_content_planning_summary=_cluster_content_summary(clusters, briefs),
        operational_action_queue=actions,
        evidence_source_references=evidence_refs,
        limitations_and_assumptions=limitations,
    )


def _input_value(payload: dict[str, Any], name: str) -> Any:
    for key in INPUT_ALIASES[name]:
        if key in payload:
            return payload[key]
    if name == "technical" and "findings" in payload:
        return payload
    return None


def _coverage_item(name: str, value: Any) -> SeniorReportCoverageItem:
    present = value is not None
    return SeniorReportCoverageItem(
        input_name=name,
        present=present,
        item_count=_item_count(name, value) if present else 0,
        limitation=None if present else f"Optional input '{name}' was not provided; related report sections use available local evidence only.",
    )


def _item_count(name: str, value: Any) -> int:
    if isinstance(value, list):
        return len([item for item in value if isinstance(item, dict)])
    if not isinstance(value, dict):
        return 0
    if name in {"technical", "content_quality", "entity_readiness", "internal_links", "ai_readiness"}:
        return len(_items(value, "findings"))
    if name == "main_content":
        return len(_items(value, "pages"))
    if name == "search_console":
        return _int_or_zero(_nested(value, ("aggregate", "rows"))) or len(_items(value, "rows"))
    if name == "opportunities":
        return len(_items(value, "opportunities"))
    if name == "content_briefs":
        return len(_items(value, "briefs"))
    if name == "content_clusters":
        return len(_items(value, "clusters"))
    return 0


def _all_findings(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []
    for source in ("technical", "content_quality", "entity_readiness", "internal_links"):
        for index, finding in enumerate(_items(inputs[source], "findings"), start=1):
            item = dict(finding)
            item.setdefault("_report_source", source)
            item.setdefault("id", f"{source}.finding_{index}")
            findings.append(item)
    return findings


def _executive_summary(
    available_inputs: list[str],
    missing_inputs: list[str],
    findings: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
    actions: list[SeniorOperationalAction],
) -> SeniorReportSummary:
    top_priority = _top_priority([_priority(item) for item in findings + opportunities])
    statements = [
        f"Report generated from {len(available_inputs)} available local input group(s).",
        f"Detected {len(findings)} audit finding(s) and {len(opportunities)} opportunity item(s).",
        "No traffic, ranking, revenue, ROI or AI visibility forecast is included.",
    ]
    if missing_inputs:
        statements.append(f"Missing optional inputs: {', '.join(missing_inputs)}.")

    return SeniorReportSummary(
        headline=_headline(top_priority, len(findings), len(opportunities)),
        available_inputs=available_inputs,
        missing_inputs=missing_inputs,
        total_findings=len(findings),
        total_opportunities=len(opportunities),
        total_operational_actions=len(actions),
        top_priority=top_priority,
        statements=statements,
    )


def _headline(top_priority: str | None, finding_count: int, opportunity_count: int) -> str:
    if finding_count == 0 and opportunity_count == 0:
        return "No local findings or opportunities were available for prioritization."
    if top_priority in {"critical", "high"}:
        return f"Local audit evidence contains {top_priority} priority items requiring operator review."
    return "Local audit evidence is available for operational prioritization."


def _health_snapshot(
    inputs: dict[str, Any],
    findings: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
    briefs: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    ai_findings: list[dict[str, Any]],
) -> SeniorHealthSnapshot:
    by_severity = Counter(_priority(item) for item in findings if _priority(item))
    return SeniorHealthSnapshot(
        technical_findings=len(_items(inputs["technical"], "findings")),
        content_quality_findings=len(_items(inputs["content_quality"], "findings")),
        entity_readiness_findings=len(_items(inputs["entity_readiness"], "findings")),
        internal_link_findings=len(_items(inputs["internal_links"], "findings")),
        opportunity_count=len(opportunities),
        content_brief_count=len(briefs),
        content_cluster_count=len(clusters),
        ai_readiness_targets=_int_or_zero(_nested(inputs["ai_readiness"], ("summary", "total_targets"))) or len(ai_findings),
        ai_readiness_average_score=_float_or_none(_nested(inputs["ai_readiness"], ("summary", "average_readiness_score"))),
        search_console_rows=_int_or_zero(_nested(inputs["search_console"], ("aggregate", "rows"))) or len(_items(inputs["search_console"], "rows")),
        by_severity=dict(sorted(by_severity.items(), key=lambda item: SEVERITY_ORDER.get(item[0], 99))),
    )


def _top_risks(
    findings: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
    ai_findings: list[dict[str, Any]],
) -> list[SeniorPriorityRisk]:
    candidates = []
    for item in findings:
        candidates.append(_risk_item(item, _source(item), _id(item), _title(item)))
    for item in opportunities:
        candidates.append(_risk_item(item, "opportunities", _id(item), _title(item)))
    for item in ai_findings:
        candidates.append(_risk_item(item, "ai_readiness", _id(item), _title(item, fallback="AI readiness target")))
    candidates.sort(key=lambda item: (SEVERITY_ORDER.get(item.priority, 99), item.source, item.id))
    return candidates[:10]


def _risk_item(item: dict[str, Any], source: str, item_id: str, title: str) -> SeniorPriorityRisk:
    return SeniorPriorityRisk(
        id=item_id,
        source=source,
        title=title,
        priority=_priority(item) or "info",
        risk=_string_or_none(item.get("risk")) or _first_risk_text(item),
        next_action=_string_or_none(item.get("next_action")) or _first_next_action(item),
        page_url=_page_url(item),
        source_ids=_source_ids(item),
        evidence=_evidence(item.get("evidence")),
    )


def _opportunity_summary(opportunities: list[dict[str, Any]]) -> SeniorOpportunitySummary:
    by_priority = Counter(_priority(item) for item in opportunities if _priority(item))
    by_type = Counter(str(item.get("type")) for item in opportunities if item.get("type"))
    themes = sorted({str(item.get("type")) for item in opportunities if item.get("type")})[:10]
    return SeniorOpportunitySummary(
        total_opportunities=len(opportunities),
        by_priority=dict(sorted(by_priority.items(), key=lambda item: SEVERITY_ORDER.get(item[0], 99))),
        by_type=dict(sorted(by_type.items())),
        top_opportunity_ids=[_id(item) for item in opportunities[:10]],
        remediation_themes=themes,
    )


def _ai_geo_summary(ai_input: Any, ai_findings: list[dict[str, Any]]) -> SeniorAIReadinessSummary:
    summary = ai_input.get("summary") if isinstance(ai_input, dict) and isinstance(ai_input.get("summary"), dict) else {}
    limitations = []
    if ai_input is None:
        limitations.append("AI readiness simulation output was not provided; AI/GEO readiness is not inferred.")
    for finding in ai_findings:
        limitations.extend(str(item) for item in finding.get("limitations", []) if item)
    return SeniorAIReadinessSummary(
        targets=_int_or_zero(summary.get("total_targets")) or len(ai_findings),
        average_score=_float_or_none(summary.get("average_readiness_score")),
        by_readiness_band=dict(sorted(_dict_or_empty(summary.get("by_readiness_band")).items())),
        by_priority=dict(sorted(_dict_or_empty(summary.get("by_priority")).items(), key=lambda item: SEVERITY_ORDER.get(item[0], 99))),
        explicit_limitations=_unique(limitations),
    )


def _cluster_content_summary(clusters: list[dict[str, Any]], briefs: list[dict[str, Any]]) -> SeniorClusterContentSummary:
    limitations = []
    for item in clusters + briefs:
        limitations.extend(str(value) for value in item.get("limitations", []) if value)
    return SeniorClusterContentSummary(
        total_clusters=len(clusters),
        total_briefs=len(briefs),
        total_link_recommendations=sum(len(_items(cluster, "internal_link_recommendations")) for cluster in clusters),
        cluster_ids=[_id(cluster) for cluster in clusters if _id(cluster)],
        brief_ids=[_id(brief) for brief in briefs if _id(brief)],
        limitations=_unique(limitations),
    )


def _operational_actions(
    findings: list[dict[str, Any]],
    opportunities: list[dict[str, Any]],
    briefs: list[dict[str, Any]],
    ai_findings: list[dict[str, Any]],
) -> list[SeniorOperationalAction]:
    actions = []
    for item in findings:
        action = _string_or_none(item.get("next_action"))
        if action:
            actions.append(_action_item(item, _source(item), _id(item), action))
    for item in opportunities:
        action = _string_or_none(item.get("next_action"))
        if action:
            actions.append(_action_item(item, "opportunities", _id(item), action))
    for brief in briefs:
        for risk_action in _items(brief, "risks_and_next_actions"):
            merged = dict(risk_action)
            merged.setdefault("priority", brief.get("priority"))
            merged.setdefault("page_url", brief.get("target_url") or brief.get("proposed_url"))
            merged.setdefault("source_ids", _source_ids(brief))
            actions.append(_action_item(merged, "content_briefs", _id(brief), str(risk_action.get("next_action") or "Review content brief action.")))
    for finding in ai_findings:
        for risk_action in _items(finding, "risks_and_next_actions"):
            merged = dict(risk_action)
            merged.setdefault("page_url", finding.get("page_url"))
            merged.setdefault("source_ids", _source_ids(finding))
            actions.append(_action_item(merged, "ai_readiness", _id(finding), str(risk_action.get("next_action") or "Review AI readiness action.")))

    actions.sort(key=lambda item: (SEVERITY_ORDER.get(item.priority, 99), item.source, item.id, item.action))
    return actions[:50]


def _action_item(item: dict[str, Any], source: str, item_id: str, action: str) -> SeniorOperationalAction:
    return SeniorOperationalAction(
        id=f"action.{source}.{item_id}",
        priority=_priority(item) or "info",
        source=source,
        action=action,
        page_url=_page_url(item),
        risk=_string_or_none(item.get("risk")),
        owner_hint=_owner_hint(source),
        source_ids=_source_ids(item) or [item_id],
        evidence=_evidence(item.get("evidence")),
    )


def _evidence_references(*groups: list[dict[str, Any]]) -> list[SeniorEvidenceReference]:
    refs = []
    for group in groups:
        for item in group:
            evidence = _evidence(item.get("evidence"))
            source_ids = _source_ids(item) or [_id(item)]
            for source_id in source_ids:
                if evidence or source_id:
                    refs.append(
                        SeniorEvidenceReference(
                            source=_source(item),
                            source_id=source_id,
                            page_url=_page_url(item),
                            evidence=evidence,
                        )
                    )
    refs.sort(key=lambda item: (item.source, item.source_id or "", item.page_url or ""))
    return refs[:100]


def _limitations(
    coverage: list[SeniorReportCoverageItem],
    inputs: dict[str, Any],
    ai_findings: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    briefs: list[dict[str, Any]],
) -> list[str]:
    limitations = [item.limitation for item in coverage if item.limitation]
    limitations.append("Report is generated only from local JSON inputs and does not call LLMs or external APIs.")
    limitations.append("Report does not forecast rankings, traffic, revenue, ROI, conversions or AI visibility.")
    if inputs["search_console"] is None:
        limitations.append("Search Console analytics were not provided; demand/performance interpretation is limited.")
    for item in ai_findings + clusters + briefs:
        limitations.extend(str(value) for value in item.get("limitations", []) if value)
    return _unique(limitations)


def _items(value: Any, key: str) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        target = value.get(key)
        if isinstance(target, list):
            return [item for item in target if isinstance(item, dict)]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _nested(value: Any, keys: tuple[str, ...]) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _priority(item: dict[str, Any]) -> str | None:
    value = item.get("priority") or item.get("severity") or item.get("readiness_priority")
    if isinstance(value, str) and value in SEVERITY_ORDER:
        return value
    return None


def _top_priority(priorities: list[str | None]) -> str | None:
    valid = [priority for priority in priorities if priority]
    if not valid:
        return None
    return sorted(valid, key=lambda item: SEVERITY_ORDER.get(item, 99))[0]


def _source(item: dict[str, Any]) -> str:
    return str(item.get("_report_source") or item.get("source") or "local_input")


def _id(item: dict[str, Any]) -> str:
    return str(item.get("id") or item.get("target_id") or item.get("source_id") or "unknown")


def _title(item: dict[str, Any], fallback: str = "Untitled item") -> str:
    return str(item.get("title") or item.get("risk") or item.get("target_id") or fallback)


def _page_url(item: dict[str, Any]) -> str | None:
    return _string_or_none(item.get("page_url") or item.get("url") or item.get("target_url") or item.get("proposed_url"))


def _source_ids(item: dict[str, Any]) -> list[str]:
    values = []
    for key in ("source_ids", "source_opportunity_ids", "source_finding_ids", "source_page_ids", "source_brief_ids"):
        raw = item.get(key)
        if isinstance(raw, list):
            values.extend(str(value) for value in raw if value)
    for ref in item.get("source_refs", []):
        if isinstance(ref, dict) and ref.get("source_id"):
            values.append(str(ref["source_id"]))
    for key in ("finding_id", "source_id"):
        if item.get(key):
            values.append(str(item[key]))
    return _unique(values)


def _first_risk_text(item: dict[str, Any]) -> str | None:
    actions = _items(item, "risks_and_next_actions")
    return _string_or_none(actions[0].get("risk")) if actions else None


def _first_next_action(item: dict[str, Any]) -> str | None:
    actions = _items(item, "risks_and_next_actions")
    return _string_or_none(actions[0].get("next_action")) if actions else None


def _owner_hint(source: str) -> str:
    if source in {"technical", "internal_links"}:
        return "technical/operator"
    if source in {"content_quality", "content_briefs", "entity_readiness"}:
        return "content/SEO"
    if source == "ai_readiness":
        return "SEO/GEO"
    return "operator"


def _evidence(raw: Any) -> list[Evidence]:
    if not isinstance(raw, list):
        return []
    evidence = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            evidence.append(Evidence.model_validate(item))
        except ValidationError:
            continue
    return evidence


def _dict_or_empty(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {str(key): _int_or_zero(count) for key, count in value.items()}


def _int_or_zero(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _float_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return None


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _unique(values: list[str | None]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
