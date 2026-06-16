from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from geo_seo_engine.content_clusters.models import (
    ContentCluster,
    ContentClusterLinkRecommendation,
    ContentClusterPlannerResult,
    ContentClusterSourceRef,
    ContentClusterSummary,
)
from geo_seo_engine.core.models import Evidence
from geo_seo_engine.core.url import normalize_url

INPUT_KEYS = {
    "pages": ("main_content", "content_extraction", "content_extract"),
    "briefs": ("content_briefs", "content_brief", "briefs"),
    "opportunities": ("opportunities", "opportunity_engine"),
    "entity_readiness": ("entity_readiness", "entity", "audit_entity_readiness"),
    "internal_links": ("internal_links", "internal_link_graph", "audit_internal_links"),
    "search_console": ("search_console", "search_console_analytics", "gsc"),
}

PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
STOPWORDS = {
    "a",
    "an",
    "and",
    "best",
    "for",
    "guide",
    "how",
    "in",
    "of",
    "page",
    "the",
    "to",
    "what",
    "with",
}


@dataclass
class ClusterItem:
    source_type: str
    source_id: str
    page_url: str | None = None
    title: str | None = None
    primary_entity: str | None = None
    topics: list[str] = field(default_factory=list)
    priority: str | None = None
    status: str | None = None
    type: str | None = None
    finding_id: str | None = None
    source_opportunity_ids: list[str] = field(default_factory=list)
    source_finding_ids: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)


def plan_content_clusters(payload: dict[str, Any]) -> ContentClusterPlannerResult:
    """Group local content planning signals into deterministic, auditable clusters."""
    pages = _extract_pages(payload)
    entity_audits = _extract_entity_audits(payload)
    opportunities = _extract_opportunities(payload)
    briefs = _extract_briefs(payload)
    search_console_topics = _extract_search_console_topics(payload)
    internal_links = _extract_internal_links(payload)
    inputs_present, inputs_missing = _input_coverage(payload)

    items = _items_from_pages(pages, entity_audits, search_console_topics)
    items.extend(_items_from_opportunities(opportunities, pages, entity_audits))
    items.extend(_items_from_briefs(briefs, pages, entity_audits))

    grouped: dict[str, list[ClusterItem]] = defaultdict(list)
    for item in items:
        grouped[_cluster_key(item)].append(item)

    clusters = [
        _build_cluster(key, group_items, internal_links, inputs_missing)
        for key, group_items in grouped.items()
    ]
    clusters.sort(key=lambda cluster: (cluster.label.lower(), cluster.id))

    return ContentClusterPlannerResult(
        clusters=clusters,
        summary=_summary(clusters, items, inputs_present, inputs_missing),
    )


def _extract_pages(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pages = {}
    for keys in (INPUT_KEYS["pages"], ("content_quality", "content"), INPUT_KEYS["entity_readiness"]):
        container = _first_dict(payload, keys)
        raw_pages = container.get("pages") if container else None
        if not isinstance(raw_pages, list):
            continue
        for index, page in enumerate(raw_pages, start=1):
            if not isinstance(page, dict):
                continue
            page_url = _normalize_page(_string(page.get("page_url") or page.get("url") or page.get("normalized_url")))
            if not page_url:
                continue
            copied = dict(page)
            copied.setdefault("id", f"page.{_slug(page_url)}.{index}")
            pages[page_url] = copied

    internal_links = _first_dict(payload, INPUT_KEYS["internal_links"])
    raw_link_pages = internal_links.get("pages") if internal_links else None
    if isinstance(raw_link_pages, list):
        for index, page in enumerate(raw_link_pages, start=1):
            if not isinstance(page, dict):
                continue
            page_url = _normalize_page(_string(page.get("normalized_url") or page.get("url") or page.get("page_url")))
            if page_url:
                pages.setdefault(page_url, {"id": f"page.{_slug(page_url)}.{index}", **page})
    return pages


def _extract_entity_audits(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    container = _first_dict(payload, INPUT_KEYS["entity_readiness"])
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


def _extract_opportunities(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload.get("opportunities"), list):
        return [item for item in payload["opportunities"] if isinstance(item, dict)]
    engine = payload.get("opportunity_engine")
    if isinstance(engine, dict) and isinstance(engine.get("opportunities"), list):
        return [item for item in engine["opportunities"] if isinstance(item, dict)]
    return []


def _extract_briefs(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload.get("briefs"), list):
        return [item for item in payload["briefs"] if isinstance(item, dict)]
    for key in ("content_briefs", "content_brief"):
        container = payload.get(key)
        if isinstance(container, dict) and isinstance(container.get("briefs"), list):
            return [item for item in container["briefs"] if isinstance(item, dict)]
    return []


def _extract_search_console_topics(payload: dict[str, Any]) -> dict[str, list[str]]:
    container = _first_dict(payload, INPUT_KEYS["search_console"])
    if not container:
        return {}
    queries_by_page: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in container.get("rows", []):
        if not isinstance(row, dict):
            continue
        page = _normalize_page(_string(row.get("normalized_page") or row.get("page")))
        query = _string(row.get("query"))
        if page and query:
            queries_by_page[page].append(row)
    output = {}
    for page, rows in queries_by_page.items():
        ordered = sorted(rows, key=lambda row: (-_int(row.get("impressions")), str(row.get("query") or "")))
        output[page] = [_string(row.get("query")) for row in ordered[:3] if _string(row.get("query"))]
    return output


def _extract_internal_links(payload: dict[str, Any]) -> set[tuple[str, str]]:
    container = _first_dict(payload, INPUT_KEYS["internal_links"])
    edges = set()
    if not container:
        return edges
    for edge in container.get("edges", []):
        if not isinstance(edge, dict):
            continue
        source = _normalize_page(_string(edge.get("source_url")))
        target = _normalize_page(_string(edge.get("target_url")))
        if source and target:
            edges.add((source, target))
    return edges


def _items_from_pages(
    pages: dict[str, dict[str, Any]],
    entity_audits: dict[str, dict[str, Any]],
    search_console_topics: dict[str, list[str]],
) -> list[ClusterItem]:
    items = []
    for page_url, page in pages.items():
        entity_audit = entity_audits.get(page_url, {})
        title = _string(page.get("title")) or _h1(page) or _topic_from_url(page_url)
        primary_entity = _string(entity_audit.get("primary_entity") or page.get("primary_entity"))
        topics = _strings(entity_audit.get("topic_terms")) + _strings(page.get("topic_terms")) + search_console_topics.get(page_url, [])
        items.append(
            ClusterItem(
                source_type="page",
                source_id=_string(page.get("id")) or f"page.{_slug(page_url)}",
                page_url=page_url,
                title=title,
                primary_entity=primary_entity,
                topics=_unique(topics),
                status=_page_status(page),
                type="page",
            )
        )
    return items


def _items_from_opportunities(
    opportunities: list[dict[str, Any]], pages: dict[str, dict[str, Any]], entity_audits: dict[str, dict[str, Any]]
) -> list[ClusterItem]:
    items = []
    for index, opportunity in enumerate(opportunities, start=1):
        page_url = _normalize_page(_string(opportunity.get("page_url") or opportunity.get("url")))
        page = pages.get(page_url or "", {})
        entity_audit = entity_audits.get(page_url or "", {})
        source_id = _string(opportunity.get("id")) or f"opportunity.{index}"
        finding_id = _string(opportunity.get("finding_id"))
        items.append(
            ClusterItem(
                source_type="opportunity",
                source_id=source_id,
                page_url=page_url,
                title=_string(opportunity.get("title")) or _string(page.get("title")),
                primary_entity=_string(entity_audit.get("primary_entity") or page.get("primary_entity")),
                topics=_strings(entity_audit.get("topic_terms")) + [_string(opportunity.get("type")) or ""],
                priority=_normalized_priority(opportunity.get("priority")),
                status="opportunity",
                type=_string(opportunity.get("type")) or "opportunity",
                finding_id=finding_id,
                source_opportunity_ids=[source_id],
                source_finding_ids=[finding_id] if finding_id else [],
                evidence=_evidence(opportunity.get("evidence")),
            )
        )
    return items


def _items_from_briefs(
    briefs: list[dict[str, Any]], pages: dict[str, dict[str, Any]], entity_audits: dict[str, dict[str, Any]]
) -> list[ClusterItem]:
    items = []
    for index, brief in enumerate(briefs, start=1):
        page_url = _normalize_page(_string(brief.get("target_url") or brief.get("page_url")))
        page = pages.get(page_url or "", {})
        entity_audit = entity_audits.get(page_url or "", {})
        topics = [_string(brief.get("primary_topic_entity_cue")) or ""] + _strings(brief.get("content_gaps"))[:3]
        items.append(
            ClusterItem(
                source_type="brief",
                source_id=_string(brief.get("id")) or f"brief.{index}",
                page_url=page_url,
                title=_string(brief.get("primary_topic_entity_cue")) or _string(page.get("title")) or _string(brief.get("proposed_url")),
                primary_entity=_string(brief.get("primary_topic_entity_cue") or entity_audit.get("primary_entity")),
                topics=topics + _strings(entity_audit.get("topic_terms")),
                priority=_normalized_priority(brief.get("priority")),
                status=_string(brief.get("brief_type")) or "brief",
                type=_string(brief.get("brief_type")) or "brief",
                source_opportunity_ids=_strings(brief.get("source_opportunity_ids")),
                source_finding_ids=_strings(brief.get("source_finding_ids")),
                evidence=_evidence(brief.get("evidence")),
            )
        )
    return items


def _build_cluster(
    key: str,
    items: list[ClusterItem],
    internal_links: set[tuple[str, str]],
    inputs_missing: list[str],
) -> ContentCluster:
    page_urls = _unique([item.page_url for item in items if item.page_url])
    brief_ids = _unique([item.source_id for item in items if item.source_type == "brief"])
    opportunity_ids = _unique(
        [item.source_id for item in items if item.source_type == "opportunity"]
        + [source_id for item in items for source_id in item.source_opportunity_ids]
    )
    finding_ids = _unique(
        [item.finding_id for item in items if item.finding_id]
        + [source_id for item in items for source_id in item.source_finding_ids]
    )
    entities = _unique([item.primary_entity for item in items if item.primary_entity])
    topics = _unique([topic for item in items for topic in item.topics if topic])[:20]
    pillar, pillar_reason = _pillar_page(page_urls, items, internal_links)
    supporting_pages = [url for url in page_urls if url != pillar]
    source_refs = [
        ContentClusterSourceRef(source_type=item.source_type, source_id=item.source_id, page_url=item.page_url)
        for item in items
    ]
    label = _label(entities, topics, items, key)
    evidence = _unique_evidence([evidence for item in items for evidence in item.evidence])

    return ContentCluster(
        id="content_cluster." + _slug(key)[:80],
        label=label,
        pillar_page_url=pillar,
        pillar_reason=pillar_reason,
        supporting_page_urls=supporting_pages,
        supporting_brief_ids=brief_ids,
        entities=entities,
        topics=topics,
        internal_link_recommendations=_link_recommendations(pillar, supporting_pages, label, internal_links, source_refs),
        source_refs=source_refs,
        source_page_ids=_unique([item.source_id for item in items if item.source_type == "page"]),
        source_brief_ids=brief_ids,
        source_opportunity_ids=opportunity_ids,
        source_finding_ids=finding_ids,
        evidence=evidence,
        confidence=_confidence(items, evidence, page_urls),
        limitations=_limitations(inputs_missing, items, page_urls, evidence),
    )


def _cluster_key(item: ClusterItem) -> str:
    cue = item.primary_entity or _first_topic(item.topics) or item.title or item.page_url or item.source_id
    tokens = _tokens(cue)
    if tokens:
        return " ".join(tokens[:3])
    return _slug(cue or item.source_id)


def _pillar_page(
    page_urls: list[str], items: list[ClusterItem], internal_links: set[tuple[str, str]]
) -> tuple[str | None, str | None]:
    if not page_urls:
        return None, None
    scores = {}
    for url in page_urls:
        inbound = sum(1 for _, target in internal_links if target == url)
        outbound = sum(1 for source, _ in internal_links if source == url)
        title = " ".join(item.title or "" for item in items if item.page_url == url).lower()
        score = inbound * 3 + outbound * 2 - _path_depth(url)
        if re.search(r"\b(guide|docs|documentation|hub|overview|learn)\b", title):
            score += 4
        scores[url] = score
    pillar = sorted(page_urls, key=lambda url: (-scores[url], _path_depth(url), url))[0]
    if len(page_urls) == 1 and scores[pillar] <= 0:
        return pillar, "Only page with cluster evidence; hub candidacy is limited."
    return pillar, "Selected deterministically from internal-link degree, URL depth and hub-like title cues."


def _link_recommendations(
    pillar: str | None,
    supporting_pages: list[str],
    label: str,
    internal_links: set[tuple[str, str]],
    source_refs: list[ContentClusterSourceRef],
) -> list[ContentClusterLinkRecommendation]:
    if not pillar:
        return []
    source_ids = _unique([ref.source_id for ref in source_refs])
    recommendations = []
    for page in supporting_pages:
        if (pillar, page) not in internal_links:
            recommendations.append(
                ContentClusterLinkRecommendation(
                    source_url=pillar,
                    target_url=page,
                    anchor_text=_anchor_from_url(page),
                    reason="Cluster pages share deterministic entity/topic evidence and no existing edge was provided from the pillar candidate.",
                    source_ids=source_ids,
                    confidence=0.75,
                )
            )
        if (page, pillar) not in internal_links:
            recommendations.append(
                ContentClusterLinkRecommendation(
                    source_url=page,
                    target_url=pillar,
                    anchor_text=label,
                    reason="Supporting page should reference the pillar candidate when cluster evidence is shared and no existing edge was provided.",
                    source_ids=source_ids,
                    confidence=0.75,
                )
            )
    return recommendations[:20]


def _summary(
    clusters: list[ContentCluster],
    items: list[ClusterItem],
    inputs_present: list[str],
    inputs_missing: list[str],
) -> ContentClusterSummary:
    priority_by_cluster = [_cluster_priority(cluster, items) for cluster in clusters]
    return ContentClusterSummary(
        total_clusters=len(clusters),
        total_pages=len({item.page_url for item in items if item.page_url}),
        total_briefs=len({item.source_id for item in items if item.source_type == "brief"}),
        total_link_recommendations=sum(len(cluster.internal_link_recommendations) for cluster in clusters),
        by_priority=dict(sorted(Counter(priority_by_cluster).items())),
        by_type=dict(sorted(Counter(item.type or item.source_type for item in items).items())),
        by_status=dict(sorted(Counter(item.status or item.source_type for item in items).items())),
        inputs_present=inputs_present,
        inputs_missing=inputs_missing,
    )


def _cluster_priority(cluster: ContentCluster, items: list[ClusterItem]) -> str:
    source_ids = {ref.source_id for ref in cluster.source_refs}
    priorities = [item.priority for item in items if item.source_id in source_ids and item.priority in PRIORITY_RANK]
    if not priorities:
        return "low"
    return sorted(priorities, key=lambda value: PRIORITY_RANK[value])[0]


def _input_coverage(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    present = []
    missing = []
    for name, keys in INPUT_KEYS.items():
        is_present = any(key in payload for key in keys)
        (present if is_present else missing).append(name)
    return present, missing


def _label(entities: list[str], topics: list[str], items: list[ClusterItem], key: str) -> str:
    for candidate in entities + topics + [item.title for item in items if item.title]:
        text = _string(candidate)
        if text:
            return text
    return key.replace("-", " ").title()


def _confidence(items: list[ClusterItem], evidence: list[Evidence], page_urls: list[str]) -> float:
    score = 0.35
    if page_urls:
        score += 0.2
    if any(item.primary_entity for item in items):
        score += 0.2
    if evidence:
        score += 0.15
    if len({item.source_type for item in items}) > 1:
        score += 0.1
    return round(min(1.0, score), 2)


def _limitations(inputs_missing: list[str], items: list[ClusterItem], page_urls: list[str], evidence: list[Evidence]) -> list[str]:
    limitations = [f"Input not provided: {name}." for name in inputs_missing]
    if not page_urls:
        limitations.append("Cluster has no concrete page URL; membership depends on brief or opportunity cues only.")
    if not any(item.primary_entity for item in items):
        limitations.append("No primary entity cue was available; label and membership use titles, topics or URL slugs.")
    if not evidence:
        limitations.append("No structured evidence records were available for this cluster.")
    return _unique(limitations)


def _page_status(page: dict[str, Any]) -> str:
    if page.get("is_orphan") is True:
        return "orphan"
    if page.get("is_hub") is True:
        return "hub_candidate"
    if page.get("status_code") and int(page.get("status_code") or 0) >= 400:
        return "http_error"
    return "existing_page"


def _h1(page: dict[str, Any]) -> str | None:
    headings = page.get("headings")
    if not isinstance(headings, list):
        return None
    for heading in headings:
        if isinstance(heading, dict) and heading.get("level") == 1 and heading.get("text"):
            return str(heading["text"])
    return None


def _first_topic(topics: list[str]) -> str | None:
    for topic in topics:
        if topic:
            return topic
    return None


def _topic_from_url(value: str) -> str | None:
    try:
        path = normalize_url(value).path.strip("/")
    except ValueError:
        return None
    if not path:
        return None
    return path.split("/")[-1].replace("-", " ").replace("_", " ")


def _anchor_from_url(value: str) -> str:
    return _topic_from_url(value) or value


def _tokens(value: str | None) -> list[str]:
    if not value:
        return []
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    useful = [token for token in tokens if token not in STOPWORDS]
    return useful or tokens[:3]


def _path_depth(value: str) -> int:
    try:
        path = normalize_url(value).path.strip("/")
    except ValueError:
        return 99
    return len([part for part in path.split("/") if part])


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


def _unique(items: list[Any]) -> list[Any]:
    seen = set()
    output = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_string(item) for item in value if _string(item)]


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


def _normalized_priority(value: Any) -> str | None:
    text = _string(value)
    if text and text.lower() in PRIORITY_RANK:
        return text.lower()
    return None


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"
