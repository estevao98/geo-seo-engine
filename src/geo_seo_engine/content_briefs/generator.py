from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from pydantic import ValidationError

from geo_seo_engine.core.models import Evidence
from geo_seo_engine.core.url import normalize_url
from geo_seo_engine.opportunities import run_opportunity_engine
from geo_seo_engine.opportunities.models import Opportunity
from geo_seo_engine.content_briefs.models import (
    ContentBrief,
    ContentBriefGeneratorResult,
    ContentBriefLinkOpportunity,
    ContentBriefRiskAction,
    ContentBriefSummary,
)

AUDIT_INPUT_KEYS = {
    "opportunities": ("opportunities", "opportunity_engine"),
    "content_quality": ("content_quality", "content", "audit_content_quality"),
    "entity_readiness": ("entity_readiness", "entity", "audit_entity_readiness"),
    "main_content": ("main_content", "content_extraction", "content_extract"),
    "internal_links": ("internal_links", "internal_link_graph", "audit_internal_links"),
    "search_console": ("search_console", "search_console_analytics", "gsc"),
    "technical": ("technical", "technical_audit", "audit_technical"),
    "performance": ("performance", "audit_performance"),
}

PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SECTION_RULES = (
    ("entity", "Define the primary entity and related entities"),
    ("content", "Cover the user task, decision criteria and supporting evidence"),
    ("crawlability", "Clarify crawl/indexing status before content expansion"),
    ("technical", "Document technical constraints that affect the page"),
    ("performance", "Address performance constraints that may affect usefulness"),
)


def generate_content_briefs(payload: dict[str, Any]) -> ContentBriefGeneratorResult:
    """Build deterministic planning briefs from local audit and opportunity JSON."""
    opportunities = _extract_opportunities(payload)
    findings = _extract_all_findings(payload)
    pages_by_url = _extract_pages(payload)
    entity_audits_by_url = _extract_entity_page_audits(payload)
    internal_links = _extract_internal_link_opportunities(payload)
    search_console = _extract_search_console(payload)
    inputs_present, inputs_missing = _input_coverage(payload, opportunities)

    grouped: dict[str, list[Opportunity]] = defaultdict(list)
    for opportunity in opportunities:
        grouped[opportunity.page_url or _proposed_key(opportunity)].append(opportunity)

    if not grouped:
        for page_url in pages_by_url:
            grouped[page_url] = []

    briefs = [
        _build_brief(
            page_key=page_key,
            opportunities=items,
            findings=findings,
            pages_by_url=pages_by_url,
            entity_audits_by_url=entity_audits_by_url,
            internal_links=internal_links,
            search_console=search_console,
            global_limitations=_limitations(inputs_missing),
        )
        for page_key, items in grouped.items()
    ]
    briefs.sort(key=lambda brief: (PRIORITY_RANK[brief.priority], brief.target_url or brief.proposed_url or "", brief.id))

    return ContentBriefGeneratorResult(
        briefs=briefs,
        summary=_summary(briefs, inputs_present, inputs_missing),
    )


def _extract_opportunities(payload: dict[str, Any]) -> list[Opportunity]:
    raw_items = None
    if isinstance(payload.get("opportunities"), list):
        raw_items = payload["opportunities"]
    elif isinstance(payload.get("opportunity_engine"), dict) and isinstance(payload["opportunity_engine"].get("opportunities"), list):
        raw_items = payload["opportunity_engine"]["opportunities"]

    if raw_items is not None:
        opportunities = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            try:
                opportunities.append(Opportunity.model_validate(item))
            except ValidationError:
                continue
        return opportunities

    try:
        return run_opportunity_engine(payload).opportunities
    except (KeyError, TypeError, ValueError, ValidationError):
        return []


def _build_brief(
    page_key: str,
    opportunities: list[Opportunity],
    findings: dict[str, dict[str, Any]],
    pages_by_url: dict[str, dict[str, Any]],
    entity_audits_by_url: dict[str, dict[str, Any]],
    internal_links: list[ContentBriefLinkOpportunity],
    search_console: dict[str, Any],
    global_limitations: list[str],
) -> ContentBrief:
    target_url = page_key if page_key.startswith("http") else None
    related_findings = [findings[item.finding_id] for item in opportunities if item.finding_id in findings]
    page = pages_by_url.get(target_url or "", {})
    entity_audit = entity_audits_by_url.get(target_url or "", {})
    source_finding_ids = _unique([item.finding_id for item in opportunities])
    source_opportunity_ids = _unique([item.id for item in opportunities])
    evidence = _unique_evidence(
        [evidence for item in opportunities for evidence in item.evidence]
        + [evidence for finding in related_findings for evidence in _evidence(finding.get("evidence"))]
    )
    risk_actions = _risk_actions(opportunities, related_findings)
    priority = _brief_priority(opportunities)
    topic = _topic_cue(page_key, opportunities, page, entity_audit, search_console)
    query = _top_query(target_url, search_console)

    return ContentBrief(
        id=_brief_id(target_url or page_key, source_opportunity_ids, source_finding_ids),
        target_url=target_url,
        proposed_url=None if target_url else page_key,
        brief_type=_brief_type(target_url, opportunities),
        priority=priority,
        primary_topic_entity_cue=topic,
        search_intent_cue=_search_intent(query or topic),
        audience_usefulness_notes=_audience_notes(opportunities, page, query),
        required_sections=_required_sections(opportunities, related_findings, page, entity_audit),
        content_gaps=_content_gaps(opportunities, related_findings, page, entity_audit),
        questions_to_answer=_questions(opportunities, related_findings, topic),
        internal_link_opportunities=_links_for_page(target_url, internal_links),
        risks_and_next_actions=risk_actions,
        source_opportunity_ids=source_opportunity_ids,
        source_finding_ids=source_finding_ids,
        evidence=evidence,
        confidence=_confidence(opportunities, page, entity_audit, query),
        limitations=_brief_limitations(global_limitations, opportunities, evidence, query),
    )


def _extract_all_findings(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    findings = {}
    for source in ("technical", "content_quality", "entity_readiness", "internal_links", "performance"):
        container = _first_dict(payload, AUDIT_INPUT_KEYS[source])
        raw_findings = container.get("findings") if container else payload.get("findings") if source == "technical" else None
        if not isinstance(raw_findings, list):
            continue
        for index, finding in enumerate(raw_findings, start=1):
            if not isinstance(finding, dict):
                continue
            finding_id = str(finding.get("id") or f"{source}.finding_{index}")
            findings[finding_id] = finding
    return findings


def _extract_pages(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pages = {}
    for key_group in (("main_content", "content_extraction", "content_extract"), ("content_quality", "content"), ("entity_readiness", "entity")):
        container = _first_dict(payload, key_group)
        raw_pages = container.get("pages") if container else None
        if not isinstance(raw_pages, list):
            continue
        for page in raw_pages:
            if not isinstance(page, dict):
                continue
            page_url = _normalize_page(_string(page.get("page_url") or page.get("url") or page.get("normalized_url")))
            if page_url:
                pages[page_url] = page
    return pages


def _extract_entity_page_audits(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    container = _first_dict(payload, AUDIT_INPUT_KEYS["entity_readiness"])
    raw_audits = container.get("page_audits") if container else None
    audits = {}
    if not isinstance(raw_audits, list):
        return audits
    for audit in raw_audits:
        if not isinstance(audit, dict):
            continue
        page_url = _normalize_page(_string(audit.get("page_url") or audit.get("url")))
        if page_url:
            audits[page_url] = audit
    return audits


def _extract_internal_link_opportunities(payload: dict[str, Any]) -> list[ContentBriefLinkOpportunity]:
    container = _first_dict(payload, AUDIT_INPUT_KEYS["internal_links"])
    if not container:
        return []
    links = []
    for edge in container.get("edges", []):
        if not isinstance(edge, dict):
            continue
        target = _normalize_page(_string(edge.get("target_url")))
        if not target:
            continue
        links.append(
            ContentBriefLinkOpportunity(
                source_url=_normalize_page(_string(edge.get("source_url"))),
                target_url=target,
                anchor_text=_string(edge.get("anchor_text")),
                reason="Existing internal link edge can inform anchor and source context.",
            )
        )
    for finding in container.get("findings", []):
        if not isinstance(finding, dict):
            continue
        target = _normalize_page(_string(finding.get("page_url") or finding.get("url")))
        if not target:
            continue
        links.append(
            ContentBriefLinkOpportunity(
                target_url=target,
                reason=_string(finding.get("next_action")) or "Review internal link coverage for this page.",
                source_finding_id=_string(finding.get("id")),
            )
        )
    return links


def _extract_search_console(payload: dict[str, Any]) -> dict[str, Any]:
    container = _first_dict(payload, AUDIT_INPUT_KEYS["search_console"])
    if not container:
        return {"queries_by_page": {}, "top_queries": []}
    queries_by_page: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in container.get("rows", []):
        if not isinstance(row, dict):
            continue
        page = _normalize_page(_string(row.get("normalized_page") or row.get("page")))
        query = _string(row.get("query"))
        if page and query:
            queries_by_page[page].append(row)
    groups = container.get("groups") if isinstance(container.get("groups"), dict) else {}
    top_queries = [item for item in groups.get("by_query", []) if isinstance(item, dict)] if isinstance(groups, dict) else []
    return {"queries_by_page": queries_by_page, "top_queries": top_queries}


def _input_coverage(payload: dict[str, Any], opportunities: list[Opportunity]) -> tuple[list[str], list[str]]:
    present = []
    missing = []
    for name, keys in AUDIT_INPUT_KEYS.items():
        is_present = any(key in payload for key in keys) or (name == "opportunities" and bool(opportunities))
        (present if is_present else missing).append(name)
    return present, missing


def _risk_actions(opportunities: list[Opportunity], findings: list[dict[str, Any]]) -> list[ContentBriefRiskAction]:
    actions = [
        ContentBriefRiskAction(
            source_id=item.id,
            source_type="opportunity",
            risk=item.risk,
            next_action=item.next_action,
            evidence=item.evidence,
        )
        for item in opportunities
    ]
    opportunity_finding_ids = {item.finding_id for item in opportunities}
    for finding in findings:
        finding_id = _string(finding.get("id"))
        if not finding_id or finding_id in opportunity_finding_ids:
            continue
        actions.append(
            ContentBriefRiskAction(
                source_id=finding_id,
                source_type="finding",
                risk=_string(finding.get("risk")),
                next_action=_string(finding.get("next_action")) or "Review the finding and define the smallest safe editorial action.",
                evidence=_evidence(finding.get("evidence")),
            )
        )
    return actions


def _required_sections(
    opportunities: list[Opportunity],
    findings: list[dict[str, Any]],
    page: dict[str, Any],
    entity_audit: dict[str, Any],
) -> list[str]:
    sections = []
    categories = {item.type for item in opportunities} | {_string(finding.get("category")) or "" for finding in findings}
    for category, section in SECTION_RULES:
        if category in categories:
            sections.append(section)
    if entity_audit.get("primary_entity"):
        sections.append(f"Explain {entity_audit['primary_entity']} and its role on the page")
    headings = [heading.get("text") for heading in page.get("headings", []) if isinstance(heading, dict) and heading.get("text")]
    for heading in headings[:3]:
        sections.append(f"Validate or improve existing section: {heading}")
    return _unique(sections) or ["Define the user need, evidence, answer structure and next step for the page"]


def _content_gaps(
    opportunities: list[Opportunity],
    findings: list[dict[str, Any]],
    page: dict[str, Any],
    entity_audit: dict[str, Any],
) -> list[str]:
    gaps = []
    for item in opportunities:
        gaps.append(item.title)
    for finding in findings:
        title = _string(finding.get("title"))
        if title:
            gaps.append(title)
    if page and int(page.get("word_count") or 0) < 300:
        gaps.append("Main content may need more complete task coverage based on extracted word count")
    if entity_audit and not entity_audit.get("primary_entity"):
        gaps.append("Primary entity is not explicitly available in entity readiness data")
    return _unique(gaps)


def _questions(opportunities: list[Opportunity], findings: list[dict[str, Any]], topic: str | None) -> list[str]:
    questions = []
    if topic:
        questions.append(f"What does the user need to understand or decide about {topic}?")
    text = " ".join([item.title for item in opportunities] + [_string(finding.get("title")) or "" for finding in findings]).lower()
    if "entity" in text:
        questions.append("Which primary and secondary entities must be named, defined and supported by evidence?")
    if "thin" in text or "content" in text:
        questions.append("Which missing details, examples or criteria would make the page more useful?")
    if "link" in text or "orphan" in text:
        questions.append("Which relevant internal pages should link here, and with what descriptive anchors?")
    return _unique(questions) or ["What evidence from the available audits should guide the editor's changes?"]


def _audience_notes(opportunities: list[Opportunity], page: dict[str, Any], query: str | None) -> list[str]:
    notes = []
    if query:
        notes.append(f"Use observed Search Console query context only as evidence of demand: {query}")
    if page.get("title"):
        notes.append(f"Align usefulness with the current page title: {page['title']}")
    for item in opportunities[:3]:
        if item.rationale:
            notes.append(item.rationale[0])
    return _unique(notes) or ["Audience and usefulness notes are limited to available local findings; no persona is inferred without evidence."]


def _links_for_page(target_url: str | None, links: list[ContentBriefLinkOpportunity]) -> list[ContentBriefLinkOpportunity]:
    if not target_url:
        return []
    return [link for link in links if link.target_url == target_url][:10]


def _topic_cue(
    page_key: str,
    opportunities: list[Opportunity],
    page: dict[str, Any],
    entity_audit: dict[str, Any],
    search_console: dict[str, Any],
) -> str | None:
    if entity_audit.get("primary_entity"):
        return str(entity_audit["primary_entity"])
    headings = page.get("headings")
    if isinstance(headings, list):
        for heading in headings:
            if isinstance(heading, dict) and heading.get("level") == 1 and heading.get("text"):
                return str(heading["text"])
    if page.get("title"):
        return str(page["title"])
    query = _top_query(page_key if page_key.startswith("http") else None, search_console)
    if query:
        return query
    for item in opportunities:
        if item.title:
            return item.title
    return _topic_from_url(page_key)


def _top_query(target_url: str | None, search_console: dict[str, Any]) -> str | None:
    if target_url:
        rows = search_console.get("queries_by_page", {}).get(target_url, [])
        if rows:
            rows = sorted(rows, key=lambda row: (-int(row.get("impressions") or 0), str(row.get("query") or "")))
            return _string(rows[0].get("query"))
    top_queries = search_console.get("top_queries", [])
    if top_queries:
        top_queries = sorted(top_queries, key=lambda row: (-int(row.get("impressions") or 0), str(row.get("key") or "")))
        return _string(top_queries[0].get("key"))
    return None


def _search_intent(cue: str | None) -> str | None:
    if not cue:
        return None
    lowered = cue.lower()
    if re.search(r"\b(how|what|why|guide|tutorial|learn|examples?)\b", lowered):
        return "informational"
    if re.search(r"\b(best|pricing|price|compare|comparison|review|alternative)\b", lowered):
        return "commercial_investigation"
    if re.search(r"\b(login|docs|documentation|support)\b", lowered):
        return "navigational_or_support"
    return None


def _brief_priority(opportunities: list[Opportunity]) -> str:
    if not opportunities:
        return "low"
    return sorted((item.priority for item in opportunities), key=lambda value: PRIORITY_RANK[value])[0]


def _brief_type(target_url: str | None, opportunities: list[Opportunity]) -> str:
    if not target_url:
        return "new_page"
    if any(item.risk for item in opportunities):
        return "risk_remediation"
    return "page_refresh"


def _confidence(opportunities: list[Opportunity], page: dict[str, Any], entity_audit: dict[str, Any], query: str | None) -> float:
    if opportunities:
        base = sum(item.confidence for item in opportunities) / len(opportunities)
    else:
        base = 0.45
    bonus = 0.0
    if page:
        bonus += 0.05
    if entity_audit:
        bonus += 0.05
    if query:
        bonus += 0.05
    return round(min(1.0, base + bonus), 2)


def _limitations(inputs_missing: list[str]) -> list[str]:
    return [f"Input not provided: {name}." for name in inputs_missing]


def _brief_limitations(
    global_limitations: list[str], opportunities: list[Opportunity], evidence: list[Evidence], query: str | None
) -> list[str]:
    limitations = list(global_limitations)
    if not opportunities:
        limitations.append("No opportunity records were available for this page; brief is based on page data only.")
    if not evidence:
        limitations.append("No structured evidence records were available for this brief.")
    if not query:
        limitations.append("Search intent is not inferred when no supported query or topic cue is available.")
    return _unique(limitations)


def _summary(briefs: list[ContentBrief], inputs_present: list[str], inputs_missing: list[str]) -> ContentBriefSummary:
    return ContentBriefSummary(
        total_briefs=len(briefs),
        by_priority=dict(sorted(Counter(brief.priority for brief in briefs).items())),
        by_type=dict(sorted(Counter(brief.brief_type for brief in briefs).items())),
        inputs_present=inputs_present,
        inputs_missing=inputs_missing,
    )


def _brief_id(page_key: str, opportunity_ids: list[str], finding_ids: list[str]) -> str:
    source = opportunity_ids[0] if opportunity_ids else finding_ids[0] if finding_ids else page_key
    return "content_brief." + re.sub(r"[^a-z0-9]+", "_", source.lower()).strip("_")[:80]


def _proposed_key(opportunity: Opportunity) -> str:
    return f"proposed:{opportunity.type}:{opportunity.finding_id}"


def _topic_from_url(value: str) -> str | None:
    if not value.startswith("http"):
        return None
    path = normalize_url(value).path.strip("/")
    if not path:
        return None
    return path.split("/")[-1].replace("-", " ").replace("_", " ")


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
        key = tuple(sorted(item.model_dump(mode="json").items()))
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _unique(items: list[str]) -> list[str]:
    seen = set()
    output = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def _string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
