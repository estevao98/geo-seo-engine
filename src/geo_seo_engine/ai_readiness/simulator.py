from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from geo_seo_engine.ai_readiness.models import (
    AIReadinessComponentScore,
    AIReadinessFinding,
    AIReadinessRiskAction,
    AIReadinessSimulationResult,
    AIReadinessSummary,
)
from geo_seo_engine.core.models import Evidence
from geo_seo_engine.core.url import normalize_url

INPUT_KEYS = {
    "structured_data": ("structured_data", "structured_data_audit", "audit_structured_data"),
    "entity_readiness": ("entity_readiness", "entity", "audit_entity_readiness"),
    "main_content": ("main_content", "content_extraction", "content_extract"),
    "content_quality": ("content_quality", "content", "audit_content_quality"),
    "content_briefs": ("content_briefs", "content_brief", "briefs"),
    "content_clusters": ("content_clusters", "content_cluster", "clusters"),
    "internal_links": ("internal_links", "internal_link_graph", "audit_internal_links"),
    "technical": ("technical", "technical_audit", "audit_technical"),
    "search_console": ("search_console", "search_console_analytics", "gsc"),
}

COMPONENT_WEIGHTS = {
    "answerability": 0.18,
    "entity_clarity": 0.18,
    "evidence_support": 0.16,
    "structured_data": 0.14,
    "content_completeness": 0.2,
    "internal_context": 0.14,
}
PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@dataclass
class ReadinessTarget:
    id: str
    type: str
    page_url: str | None = None
    cluster_id: str | None = None
    pages: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)


def run_ai_readiness_simulation(payload: dict[str, Any]) -> AIReadinessSimulationResult:
    """Estimate local structural readiness for answer material without live AI checks."""
    inputs_present, inputs_missing = _input_coverage(payload)
    pages = _extract_pages(payload)
    entity_audits = _extract_entity_audits(payload)
    findings_by_page = _extract_findings_by_page(payload)
    structured_by_page, global_structured = _extract_structured_data(payload)
    briefs_by_page = _extract_briefs_by_page(payload)
    internal_pages, internal_edges = _extract_internal_links(payload)
    search_console = _extract_search_console(payload)
    clusters = _extract_clusters(payload)

    targets = _build_targets(
        pages,
        entity_audits,
        findings_by_page,
        structured_by_page,
        briefs_by_page,
        internal_pages,
        search_console,
        clusters,
    )
    simulation_findings = [
        _simulate_target(
            target=target,
            pages=pages,
            entity_audits=entity_audits,
            findings_by_page=findings_by_page,
            structured_by_page=structured_by_page,
            global_structured=global_structured,
            briefs_by_page=briefs_by_page,
            internal_pages=internal_pages,
            internal_edges=internal_edges,
            search_console=search_console,
            clusters=clusters,
            inputs_missing=inputs_missing,
        )
        for target in targets
    ]
    simulation_findings.sort(key=lambda item: (PRIORITY_RANK[item.priority], item.target_type, item.target_id))

    return AIReadinessSimulationResult(
        findings=simulation_findings,
        summary=_summary(simulation_findings, inputs_present, inputs_missing),
    )


def _build_targets(
    pages: dict[str, dict[str, Any]],
    entity_audits: dict[str, dict[str, Any]],
    findings_by_page: dict[str, list[dict[str, Any]]],
    structured_by_page: dict[str, dict[str, Any]],
    briefs_by_page: dict[str, list[dict[str, Any]]],
    internal_pages: dict[str, dict[str, Any]],
    search_console: dict[str, list[dict[str, Any]]],
    clusters: list[dict[str, Any]],
) -> list[ReadinessTarget]:
    page_urls = (
        set(pages)
        | set(entity_audits)
        | set(findings_by_page)
        | set(structured_by_page)
        | set(briefs_by_page)
        | set(internal_pages)
        | set(search_console)
    )
    targets = [
        ReadinessTarget(
            id=f"ai_readiness.page.{_slug(url)}",
            type="page",
            page_url=url,
            pages=[url],
            source_ids=_unique(
                [
                    _string(pages.get(url, {}).get("id")),
                    _string(entity_audits.get(url, {}).get("id")),
                    _string(structured_by_page.get(url, {}).get("id")),
                    _string(internal_pages.get(url, {}).get("id")),
                ]
            ),
        )
        for url in sorted(page_urls)
    ]
    for index, cluster in enumerate(clusters, start=1):
        cluster_id = _string(cluster.get("id")) or f"cluster.{index}"
        cluster_pages = _unique(
            [_normalize_page(_string(cluster.get("pillar_page_url")))]
            + [_normalize_page(_string(url)) for url in _list(cluster.get("supporting_page_urls"))]
        )
        targets.append(
            ReadinessTarget(
                id=f"ai_readiness.cluster.{_slug(cluster_id)}",
                type="cluster",
                cluster_id=cluster_id,
                page_url=_normalize_page(_string(cluster.get("pillar_page_url"))),
                pages=cluster_pages,
                source_ids=_strings(cluster.get("source_page_ids"))
                + _strings(cluster.get("source_brief_ids"))
                + _strings(cluster.get("source_finding_ids")),
                evidence=_evidence(cluster.get("evidence")),
            )
        )
    return targets


def _simulate_target(
    target: ReadinessTarget,
    pages: dict[str, dict[str, Any]],
    entity_audits: dict[str, dict[str, Any]],
    findings_by_page: dict[str, list[dict[str, Any]]],
    structured_by_page: dict[str, dict[str, Any]],
    global_structured: dict[str, Any] | None,
    briefs_by_page: dict[str, list[dict[str, Any]]],
    internal_pages: dict[str, dict[str, Any]],
    internal_edges: set[tuple[str, str]],
    search_console: dict[str, list[dict[str, Any]]],
    clusters: list[dict[str, Any]],
    inputs_missing: list[str],
) -> AIReadinessFinding:
    related_pages = target.pages or ([target.page_url] if target.page_url else [])
    page_records = [pages[url] for url in related_pages if url in pages]
    entity_records = [entity_audits[url] for url in related_pages if url in entity_audits]
    page_findings = [finding for url in related_pages for finding in findings_by_page.get(url, [])]
    page_briefs = [brief for url in related_pages for brief in briefs_by_page.get(url, [])]
    page_internal = [internal_pages[url] for url in related_pages if url in internal_pages]
    page_queries = [row for url in related_pages for row in search_console.get(url, [])]
    cluster = next((item for item in clusters if _string(item.get("id")) == target.cluster_id), {})
    structured_records = [structured_by_page[url] for url in related_pages if url in structured_by_page]
    if not structured_records and target.type == "page" and global_structured:
        structured_records = [global_structured]

    components = {
        "answerability": _answerability(page_records, page_briefs, page_queries),
        "entity_clarity": _entity_clarity(entity_records, page_records, cluster),
        "evidence_support": _evidence_support(target, page_findings, page_briefs),
        "structured_data": _structured_data(structured_records, entity_records),
        "content_completeness": _content_completeness(page_records, page_briefs, page_findings),
        "internal_context": _internal_context(target, page_internal, internal_edges, cluster),
    }
    score = round(sum(components[name].score * weight for name, weight in COMPONENT_WEIGHTS.items()))
    band = _band(score)
    risks = _risks(components)
    evidence = _unique_evidence(
        target.evidence
        + [evidence for finding in page_findings for evidence in _evidence(finding.get("evidence"))]
        + [evidence for brief in page_briefs for evidence in _evidence(brief.get("evidence"))]
    )
    source_ids = _unique(
        target.source_ids
        + [_string(finding.get("id")) for finding in page_findings]
        + [_string(brief.get("id")) for brief in page_briefs]
        + [source_id for component in components.values() for source_id in component.source_ids]
    )

    return AIReadinessFinding(
        target_id=target.id,
        target_type=target.type,
        page_url=target.page_url,
        cluster_id=target.cluster_id,
        readiness_score=score,
        readiness_band=band,
        priority=_priority(band, risks),
        answerability=components["answerability"],
        entity_clarity=components["entity_clarity"],
        evidence_support=components["evidence_support"],
        structured_data=components["structured_data"],
        content_completeness=components["content_completeness"],
        internal_context=components["internal_context"],
        risks_and_next_actions=risks,
        source_ids=source_ids,
        evidence=evidence,
        confidence=_confidence(components, inputs_missing, evidence),
        limitations=_limitations(target, inputs_missing, related_pages, evidence),
    )


def _answerability(
    pages: list[dict[str, Any]], briefs: list[dict[str, Any]], queries: list[dict[str, Any]]
) -> AIReadinessComponentScore:
    score = 0
    signals = []
    gaps = []
    source_ids = []
    if any(_h1(page) for page in pages):
        score += 25
        signals.append("Page has an H1 or primary heading cue.")
    else:
        gaps.append("No H1 or primary heading cue was available.")
    if any(_string(page.get("meta_description")) for page in pages):
        score += 15
        signals.append("Meta description can frame answer intent.")
    if any(_list(brief.get("questions_to_answer")) for brief in briefs):
        score += 25
        signals.append("Brief includes explicit questions to answer.")
        source_ids.extend(_string(brief.get("id")) for brief in briefs)
    elif queries:
        score += 15
        signals.append("Search Console query summaries provide user-question cues.")
    else:
        gaps.append("No brief questions or local query summaries were available.")
    if any(_int(page.get("paragraph_count")) >= 2 or len(_list(page.get("text_blocks"))) >= 2 for page in pages):
        score += 20
        signals.append("Main content has multiple explanatory blocks.")
    else:
        gaps.append("Main content structure is too sparse to assess answer coverage.")
    if any(_string(page.get("title")) for page in pages):
        score += 15
        signals.append("Title provides a concise topic cue.")
    return _component(score, signals, gaps, source_ids)


def _entity_clarity(
    entity_records: list[dict[str, Any]], pages: list[dict[str, Any]], cluster: dict[str, Any]
) -> AIReadinessComponentScore:
    score = 0
    signals = []
    gaps = []
    source_ids = []
    if any(_string(item.get("primary_entity")) for item in entity_records) or _list(cluster.get("entities")):
        score += 35
        signals.append("Primary entity or cluster entity cue is present.")
    else:
        gaps.append("Primary entity cue is missing.")
    if any(_list(item.get("topic_terms")) for item in entity_records) or _list(cluster.get("topics")):
        score += 20
        signals.append("Related topic/entity terms are available.")
    if any(item.get("title_h1_aligned") is True for item in entity_records):
        score += 15
        signals.append("Title and H1 alignment was confirmed by entity readiness audit.")
    elif pages:
        gaps.append("Title/H1 entity alignment was not confirmed.")
    if any(item.get("meta_content_aligned") is True for item in entity_records):
        score += 15
        signals.append("Metadata and content alignment was confirmed.")
    if any(_structured_signal(item, "has_organization") or _structured_signal(item, "has_person") for item in entity_records):
        score += 15
        signals.append("Author or organization entity signal is present.")
    else:
        gaps.append("No author or organization entity signal was available.")
    source_ids.extend(_string(item.get("id")) for item in entity_records)
    return _component(score, signals, gaps, source_ids)


def _evidence_support(
    target: ReadinessTarget, findings: list[dict[str, Any]], briefs: list[dict[str, Any]]
) -> AIReadinessComponentScore:
    evidence = target.evidence + [item for finding in findings for item in _evidence(finding.get("evidence"))]
    evidence.extend(item for brief in briefs for item in _evidence(brief.get("evidence")))
    source_ids = _unique([_string(item.get("id")) for item in findings] + [_string(item.get("id")) for item in briefs])
    signals = []
    gaps = []
    score = 0
    if evidence:
        score += min(45, 20 + len(evidence) * 10)
        signals.append("Auditable evidence records are attached.")
    else:
        gaps.append("No structured evidence records were available.")
    if source_ids:
        score += 25
        signals.append("Source IDs are preserved for traceability.")
    else:
        gaps.append("No upstream source IDs were available.")
    if any(_string(item.get("risk")) and _string(item.get("next_action")) for item in findings):
        score += 15
        signals.append("Findings include risk and next-action context.")
    if any(_list(brief.get("risks_and_next_actions")) for brief in briefs):
        score += 15
        signals.append("Briefs include risk/action planning context.")
    return _component(score, signals, gaps, source_ids)


def _structured_data(records: list[dict[str, Any]], entity_records: list[dict[str, Any]]) -> AIReadinessComponentScore:
    signals = []
    gaps = []
    score = 0
    types = _unique([schema_type for record in records for schema_type in _strings(record.get("types"))])
    valid_blocks = sum(_int(record.get("valid_json_ld_blocks")) for record in records)
    invalid_blocks = sum(_int(record.get("invalid_json_ld_blocks")) for record in records)
    if valid_blocks or types:
        score += 35
        signals.append("Valid JSON-LD or schema type signals are present.")
    else:
        gaps.append("No valid structured data signal was available.")
    if types:
        score += 20
        signals.append("Structured data types: " + ", ".join(types[:6]) + ".")
    if any(value.lower() in {"article", "webpage", "faqpage", "howto", "breadcrumblist"} for value in types):
        score += 20
        signals.append("Schema types include answer/context-friendly page structures.")
    if any(item.get("structured_data_content_aligned") is True for item in entity_records):
        score += 15
        signals.append("Structured data/content alignment was confirmed.")
    if invalid_blocks:
        gaps.append("Invalid JSON-LD blocks reduce structured data reliability.")
    elif records:
        score += 10
    return _component(score, signals, gaps, [])


def _content_completeness(
    pages: list[dict[str, Any]], briefs: list[dict[str, Any]], findings: list[dict[str, Any]]
) -> AIReadinessComponentScore:
    word_count = sum(_int(page.get("word_count")) for page in pages)
    headings = sum(_int(page.get("heading_count")) or len(_list(page.get("headings"))) for page in pages)
    score = 0
    signals = []
    gaps = []
    if word_count >= 800:
        score += 35
        signals.append("Main content has substantial word-count coverage.")
    elif word_count >= 300:
        score += 22
        signals.append("Main content has baseline word-count coverage.")
    else:
        gaps.append("Main content is missing or below baseline completeness thresholds.")
    if headings >= 2:
        score += 20
        signals.append("Heading structure provides scannable sections.")
    else:
        gaps.append("Heading structure is limited or unavailable.")
    if any(_list(brief.get("required_sections")) for brief in briefs):
        score += 20
        signals.append("Brief required sections define completeness expectations.")
    if any(_list(brief.get("content_gaps")) for brief in briefs):
        score += 10
        signals.append("Known content gaps are explicit and actionable.")
    if any(_string(finding.get("severity")) in {"critical", "high"} for finding in findings):
        gaps.append("High-priority content or technical findings may limit readiness.")
    else:
        score += 15
        signals.append("No critical/high local findings were attached to this target.")
    return _component(score, signals, gaps, [_string(brief.get("id")) for brief in briefs])


def _internal_context(
    target: ReadinessTarget,
    internal_pages: list[dict[str, Any]],
    edges: set[tuple[str, str]],
    cluster: dict[str, Any],
) -> AIReadinessComponentScore:
    inbound = sum(_int(page.get("inbound_internal_links")) for page in internal_pages)
    outbound = sum(_int(page.get("outbound_internal_links")) for page in internal_pages)
    recommendations = _list(cluster.get("internal_link_recommendations"))
    score = 0
    signals = []
    gaps = []
    if inbound > 0:
        score += 25
        signals.append("Target has inbound internal-link context.")
    else:
        gaps.append("No inbound internal-link context was available.")
    if outbound > 0:
        score += 20
        signals.append("Target links out to related internal context.")
    if target.type == "cluster" and len(target.pages) >= 2:
        existing_cluster_edges = sum(1 for source, dest in edges if source in target.pages and dest in target.pages)
        if existing_cluster_edges:
            score += 25
            signals.append("Cluster pages have provided internal edges between members.")
        elif recommendations:
            score += 15
            signals.append("Cluster planner provided internal-link recommendations.")
        else:
            gaps.append("Cluster has no provided internal edges or recommendations.")
    elif internal_pages:
        score += 20
        signals.append("Internal link metrics are available for the page.")
    if any(page.get("is_orphan") for page in internal_pages):
        gaps.append("Target includes an orphan page signal.")
    elif internal_pages:
        score += 15
    if recommendations:
        score += 15
        signals.append("Internal-link next actions are already planned.")
    return _component(score, signals, gaps, [])


def _risks(components: dict[str, AIReadinessComponentScore]) -> list[AIReadinessRiskAction]:
    mapping = {
        "answerability": ("Answerability is weak or insufficiently evidenced.", "Add explicit user questions, concise headings and explanatory sections."),
        "entity_clarity": ("Entity clarity is weak.", "Define the primary entity, related entities and visible author/publisher signals."),
        "evidence_support": ("Auditable support is limited.", "Attach source IDs, evidence records, risks and next actions from upstream audits."),
        "structured_data": ("Structured data support is weak.", "Add or fix valid JSON-LD aligned with visible page content."),
        "content_completeness": ("Content completeness is limited.", "Expand useful sections and close documented content gaps before relying on this page as answer material."),
        "internal_context": ("Internal context is limited.", "Improve contextual internal links to and from the target or cluster."),
    }
    risks = []
    for name, component in components.items():
        if component.score >= 60:
            continue
        risk, action = mapping[name]
        risks.append(
            AIReadinessRiskAction(
                priority="high" if component.score < 35 else "medium",
                risk=risk,
                next_action=action,
                source_ids=component.source_ids,
            )
        )
    return risks


def _summary(
    findings: list[AIReadinessFinding], inputs_present: list[str], inputs_missing: list[str]
) -> AIReadinessSummary:
    average = round(sum(item.readiness_score for item in findings) / len(findings), 2) if findings else 0.0
    return AIReadinessSummary(
        total_targets=len(findings),
        page_targets=sum(1 for item in findings if item.target_type == "page"),
        cluster_targets=sum(1 for item in findings if item.target_type == "cluster"),
        by_readiness_band=dict(sorted(Counter(item.readiness_band for item in findings).items())),
        by_priority=dict(sorted(Counter(item.priority for item in findings).items())),
        average_readiness_score=average,
        inputs_present=inputs_present,
        inputs_missing=inputs_missing,
    )


def _input_coverage(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    present = []
    missing = []
    for name, keys in INPUT_KEYS.items():
        is_present = any(key in payload for key in keys)
        (present if is_present else missing).append(name)
    return present, missing


def _extract_pages(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pages = {}
    for keys in (INPUT_KEYS["main_content"], INPUT_KEYS["content_quality"], INPUT_KEYS["entity_readiness"]):
        container = _first_dict(payload, keys)
        raw_pages = container.get("pages") if container else None
        if not isinstance(raw_pages, list):
            continue
        for index, page in enumerate(raw_pages, start=1):
            if not isinstance(page, dict):
                continue
            url = _normalize_page(_string(page.get("page_url") or page.get("url") or page.get("normalized_url")))
            if url:
                copied = dict(page)
                copied.setdefault("id", f"page.{_slug(url)}.{index}")
                pages[url] = copied
    return pages


def _extract_entity_audits(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    container = _first_dict(payload, INPUT_KEYS["entity_readiness"])
    raw_items = container.get("page_audits") if container else None
    output = {}
    if not isinstance(raw_items, list):
        return output
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        url = _normalize_page(_string(item.get("page_url") or item.get("url")))
        if url:
            output[url] = item
    return output


def _extract_findings_by_page(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source in ("content_quality", "entity_readiness", "internal_links", "technical"):
        container = _first_dict(payload, INPUT_KEYS[source])
        raw_findings = container.get("findings") if container else payload.get("findings") if source == "technical" else None
        if not isinstance(raw_findings, list):
            continue
        for index, finding in enumerate(raw_findings, start=1):
            if not isinstance(finding, dict):
                continue
            url = _normalize_page(_string(finding.get("page_url") or finding.get("url")))
            if not url:
                continue
            copied = dict(finding)
            copied.setdefault("id", f"{source}.finding.{index}")
            output[url].append(copied)
    return dict(output)


def _extract_structured_data(payload: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None]:
    container = _first_dict(payload, INPUT_KEYS["structured_data"])
    if not container:
        return {}, None
    by_page = {}
    raw_pages = container.get("pages")
    if isinstance(raw_pages, list):
        for item in raw_pages:
            if not isinstance(item, dict):
                continue
            url = _normalize_page(_string(item.get("page_url") or item.get("url")))
            if url:
                by_page[url] = item
    global_record = container if any(key in container for key in ("json_ld_blocks", "valid_json_ld_blocks", "types")) else None
    return by_page, global_record


def _extract_briefs_by_page(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    raw_items = None
    if isinstance(payload.get("briefs"), list):
        raw_items = payload["briefs"]
    else:
        container = _first_dict(payload, ("content_briefs", "content_brief"))
        raw_items = container.get("briefs") if container else None
    output: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not isinstance(raw_items, list):
        return {}
    for index, item in enumerate(raw_items, start=1):
        if not isinstance(item, dict):
            continue
        url = _normalize_page(_string(item.get("target_url") or item.get("page_url")))
        if url:
            copied = dict(item)
            copied.setdefault("id", f"brief.{index}")
            output[url].append(copied)
    return dict(output)


def _extract_internal_links(payload: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    container = _first_dict(payload, INPUT_KEYS["internal_links"])
    pages = {}
    edges = set()
    if not container:
        return pages, edges
    for page in container.get("pages", []):
        if not isinstance(page, dict):
            continue
        url = _normalize_page(_string(page.get("normalized_url") or page.get("url") or page.get("page_url")))
        if url:
            pages[url] = page
    for edge in container.get("edges", []):
        if not isinstance(edge, dict):
            continue
        source = _normalize_page(_string(edge.get("source_url")))
        target = _normalize_page(_string(edge.get("target_url")))
        if source and target:
            edges.add((source, target))
    return pages, edges


def _extract_search_console(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    container = _first_dict(payload, INPUT_KEYS["search_console"])
    output: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not container:
        return {}
    for row in container.get("rows", []):
        if not isinstance(row, dict):
            continue
        url = _normalize_page(_string(row.get("normalized_page") or row.get("page")))
        if url:
            output[url].append(row)
    return dict(output)


def _extract_clusters(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload.get("clusters"), list):
        return [item for item in payload["clusters"] if isinstance(item, dict)]
    container = _first_dict(payload, ("content_clusters", "content_cluster"))
    raw_items = container.get("clusters") if container else None
    if isinstance(raw_items, list):
        return [item for item in raw_items if isinstance(item, dict)]
    return []


def _component(score: int, signals: list[str], gaps: list[str], source_ids: list[str]) -> AIReadinessComponentScore:
    return AIReadinessComponentScore(
        score=max(0, min(100, score)),
        signals=_unique(signals),
        gaps=_unique(gaps),
        source_ids=_unique(source_ids),
    )


def _band(score: int) -> str:
    if score >= 80:
        return "strong"
    if score >= 60:
        return "moderate"
    if score >= 35:
        return "limited"
    return "not_ready"


def _priority(band: str, risks: list[AIReadinessRiskAction]) -> str:
    if band == "not_ready" or any(risk.priority == "high" for risk in risks[:2]):
        return "critical"
    if band == "limited":
        return "high"
    if band == "moderate":
        return "medium"
    return "low"


def _confidence(components: dict[str, AIReadinessComponentScore], inputs_missing: list[str], evidence: list[Evidence]) -> float:
    score = 0.25 + sum(0.08 for item in components.values() if item.signals)
    score += 0.15 if evidence else 0.0
    score -= min(0.3, len(inputs_missing) * 0.03)
    return round(max(0.0, min(1.0, score)), 2)


def _limitations(target: ReadinessTarget, inputs_missing: list[str], pages: list[str], evidence: list[Evidence]) -> list[str]:
    limitations = [f"Input not provided: {name}." for name in inputs_missing]
    limitations.append("This is a deterministic local structural simulation, not a live AI visibility check.")
    limitations.append("The result does not predict rankings, traffic, citations or AI Overview inclusion.")
    if not pages:
        limitations.append("No concrete page URL was available for this target.")
    if target.type == "cluster" and len(pages) < 2:
        limitations.append("Cluster-level readiness is limited because fewer than two member pages were provided.")
    if not evidence:
        limitations.append("No upstream evidence records were available for this target.")
    return _unique(limitations)


def _h1(page: dict[str, Any]) -> str | None:
    headings = page.get("headings")
    if isinstance(headings, list):
        for heading in headings:
            if isinstance(heading, dict) and _int(heading.get("level")) == 1 and _string(heading.get("text")):
                return _string(heading.get("text"))
    return _string(page.get("h1"))


def _structured_signal(item: dict[str, Any], key: str) -> bool:
    structured = item.get("structured_data")
    return isinstance(structured, dict) and structured.get(key) is True


def _first_dict(payload: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any] | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return None


def _normalize_page(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return normalize_url(value).normalized_url
    except ValueError:
        return value


def _evidence(value: Any) -> list[Evidence]:
    if not isinstance(value, list):
        return []
    evidence = []
    for item in value:
        if not isinstance(item, dict):
            continue
        try:
            evidence.append(Evidence.model_validate(item))
        except ValidationError:
            continue
    return evidence


def _unique_evidence(items: list[Evidence]) -> list[Evidence]:
    seen = set()
    output = []
    for item in items:
        key = json.dumps(item.model_dump(mode="json"), sort_keys=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    return [_string(item) for item in _list(value) if _string(item)]


def _string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _unique(items: list[Any]) -> list[Any]:
    seen = set()
    output = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"
