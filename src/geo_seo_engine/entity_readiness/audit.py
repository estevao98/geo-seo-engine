from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from bs4 import BeautifulSoup

from geo_seo_engine.content import ExtractedMainContent
from geo_seo_engine.core.models import Evidence, IssueCategory, Severity
from geo_seo_engine.entity_readiness.models import (
    EntityReadinessAuditOptions,
    EntityReadinessAuditResult,
    EntityReadinessFinding,
    EntityReadinessPageAudit,
    EntityReadinessSummary,
    EntityStructuredDataSignal,
)

_WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
_AUTHOR_RE = re.compile(r"\b(author|written by|byline|por|autor|autora)\b", re.I)
_ORG_RE = re.compile(r"\b(company|organization|publisher|empresa|organizacao)\b", re.I)
_STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "com",
    "da",
    "de",
    "do",
    "dos",
    "em",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "para",
    "the",
    "to",
    "um",
    "uma",
    "with",
}
_TARGET_TYPES = {"Organization", "Person", "Article", "WebPage", "BreadcrumbList"}
_AUTHOR_SELECTORS = ["[rel='author']", "[itemprop='author']", "[class*='author']", "[class*='byline']"]
_ORG_SELECTORS = ["[class*='publisher']", "[class*='organization']", "[class*='company']", "[itemprop='publisher']"]
_AUTHOR_META_NAMES = ("author", "article:author")
_ORG_META_NAMES = ("publisher", "article:publisher")


def run_entity_readiness_audit(
    pages: list[ExtractedMainContent],
    html_by_url: dict[str, str] | None = None,
    options: EntityReadinessAuditOptions | None = None,
    start_url: str | None = None,
) -> EntityReadinessAuditResult:
    audit_options = options or EntityReadinessAuditOptions()
    html_lookup = html_by_url or {}
    page_audits: list[EntityReadinessPageAudit] = []
    findings: list[EntityReadinessFinding] = []

    for page in pages:
        page_audit = _audit_page(page, html_lookup.get(page.page_url, ""), audit_options)
        page_audits.append(page_audit)
        findings.extend(_findings_for_page(page, page_audit, audit_options))

    return EntityReadinessAuditResult(
        start_url=start_url,
        pages=pages,
        page_audits=page_audits,
        findings=findings,
        summary=_build_summary(page_audits, findings),
    )


def _audit_page(
    page: ExtractedMainContent,
    html: str,
    options: EntityReadinessAuditOptions,
) -> EntityReadinessPageAudit:
    soup = BeautifulSoup(html or "", "html.parser")
    structured_data = _extract_structured_data_signal(soup)
    h1 = next((heading.text for heading in page.headings if heading.level == 1 and heading.text.strip()), None)
    primary_entity = h1 or _first_text(structured_data.names) or page.title
    topic_terms = _topic_terms(" ".join([page.title or "", h1 or "", page.meta_description or "", page.plain_text]))
    visible_authorship = _visible_cues(soup, _AUTHOR_RE, _AUTHOR_SELECTORS, _AUTHOR_META_NAMES)
    visible_org = _visible_cues(soup, _ORG_RE, _ORG_SELECTORS, _ORG_META_NAMES)

    title_h1_aligned = None
    if page.title and h1:
        title_h1_aligned = _aligned(page.title, h1)

    meta_content_aligned = None
    if page.meta_description:
        meta_content_aligned = _overlap(page.meta_description, page.plain_text) >= options.min_topic_token_overlap

    structured_data_content_aligned = None
    sd_text = " ".join(structured_data.names + structured_data.authors + structured_data.publishers)
    if sd_text:
        structured_data_content_aligned = _overlap(sd_text, " ".join([page.title or "", page.plain_text])) > 0

    return EntityReadinessPageAudit(
        page_url=page.page_url,
        primary_entity=primary_entity,
        topic_terms=topic_terms,
        visible_authorship_signals=visible_authorship,
        visible_organization_signals=visible_org,
        structured_data=structured_data,
        title_h1_aligned=title_h1_aligned,
        meta_content_aligned=meta_content_aligned,
        structured_data_content_aligned=structured_data_content_aligned,
    )


def _findings_for_page(
    page: ExtractedMainContent,
    audit: EntityReadinessPageAudit,
    options: EntityReadinessAuditOptions,
) -> list[EntityReadinessFinding]:
    findings: list[EntityReadinessFinding] = []
    has_author = bool(audit.visible_authorship_signals or audit.structured_data.authors or audit.structured_data.has_person)
    has_publisher = bool(
        audit.visible_organization_signals
        or audit.structured_data.publishers
        or audit.structured_data.has_organization
    )

    if not audit.primary_entity or page.word_count < options.min_content_word_count:
        findings.append(
            _finding(
                page,
                "entity.missing_primary_entity",
                "Primary page entity is unclear",
                Severity.HIGH,
                "title, H1 and main content",
                "clear primary entity with sufficient context",
                f"entity={audit.primary_entity!r}; words={page.word_count}",
                "Search and answer systems may not be able to identify what the page is primarily about.",
                "Expose one clear primary entity in the H1/title and support it with crawlable main content.",
                f"Review title, H1 and main copy on {page.page_url}.",
                0.9,
            )
        )

    if len(audit.topic_terms) < 3 or page.word_count < options.min_content_word_count:
        findings.append(
            _finding(
                page,
                "entity.unclear_topic",
                "Topic signals are too sparse",
                Severity.MEDIUM,
                "main content topic terms",
                "at least three repeated or prominent topic terms",
                ", ".join(audit.topic_terms) or "none",
                "Sparse topic terms make the page harder to classify deterministically.",
                "Add specific, user-useful copy that names the topic, related entities and use case clearly.",
                f"Expand topic context on {page.page_url}.",
                0.8,
            )
        )

    if not has_author:
        findings.append(
            _finding(
                page,
                "entity.missing_author_signal",
                "Author or source signal is missing",
                Severity.MEDIUM,
                "visible byline and structured data author",
                "visible source or author signal",
                "missing",
                "Unattributed content weakens trust, provenance and downstream entity understanding.",
                "Add a visible author/source cue and Article author structured data where appropriate.",
                f"Add author or source attribution on {page.page_url}.",
                0.85,
            )
        )

    if not has_publisher:
        findings.append(
            _finding(
                page,
                "entity.weak_publisher_signal",
                "Publisher or organization signal is weak",
                Severity.MEDIUM,
                "organization and publisher signals",
                "Organization or publisher signal",
                "missing",
                "Weak publisher signals make ownership and brand entity association less explicit.",
                "Add Organization structured data or a clear publisher/organization cue on the page.",
                f"Expose publisher or organization context for {page.page_url}.",
                0.85,
            )
        )

    if not audit.structured_data.types:
        findings.append(
            _finding(
                page,
                "entity.missing_structured_data",
                "Entity-oriented structured data is missing",
                Severity.LOW,
                "JSON-LD structured data",
                "Organization, Person, Article, WebPage or BreadcrumbList",
                "missing",
                "Missing structured data removes an explicit machine-readable entity graph from the page.",
                "Add valid JSON-LD for the page type and relevant organization, author and breadcrumb entities.",
                f"Add JSON-LD entity markup on {page.page_url}.",
                0.95,
            )
        )
    elif not set(audit.structured_data.types) & _TARGET_TYPES:
        findings.append(
            _finding(
                page,
                "entity.incomplete_structured_data_types",
                "Structured data lacks core entity types",
                Severity.LOW,
                "structured data @type",
                ", ".join(sorted(_TARGET_TYPES)),
                ", ".join(audit.structured_data.types),
                "Generic or unrelated schema types may not describe the page, author, publisher or hierarchy clearly.",
                "Use schema types that match the visible page content and provenance signals.",
                f"Review JSON-LD @type values on {page.page_url}.",
                0.9,
            )
        )

    if has_publisher and not audit.structured_data.same_as:
        findings.append(
            _finding(
                page,
                "entity.missing_same_as_signal",
                "sameAs references are missing for entity disambiguation",
                Severity.LOW,
                "Organization/Person sameAs",
                "sameAs links for known public profiles where available",
                "missing",
                "Without sameAs, public entities may be harder to disambiguate from similarly named entities.",
                "Add accurate sameAs links only for official profiles that are safe to verify and maintain.",
                f"Review whether sameAs is appropriate for {page.page_url}.",
                0.75,
            )
        )

    if audit.title_h1_aligned is False or audit.meta_content_aligned is False or audit.structured_data_content_aligned is False:
        findings.append(
            _finding(
                page,
                "entity.metadata_inconsistency",
                "Entity and topic signals are inconsistent across metadata",
                Severity.LOW,
                "title, meta description, H1, content and structured data",
                "consistent primary topic and entity",
                _alignment_summary(audit),
                "Conflicting metadata can make deterministic entity extraction less reliable.",
                "Align title, meta description, H1, body copy and structured data around the same primary entity.",
                f"Compare metadata and structured data on {page.page_url}.",
                0.75,
            )
        )

    if audit.structured_data.types and not audit.structured_data.has_breadcrumb_list:
        findings.append(
            _finding(
                page,
                "entity.missing_breadcrumb_signal",
                "Breadcrumb structured data is missing",
                Severity.INFO,
                "BreadcrumbList structured data",
                "BreadcrumbList when page hierarchy exists",
                "missing",
                "Breadcrumb markup can clarify site hierarchy and parent entities for downstream systems.",
                "Add BreadcrumbList JSON-LD when the page has a stable navigational hierarchy.",
                f"Evaluate breadcrumb markup for {page.page_url}.",
                0.7,
            )
        )

    return findings


def _finding(
    page: ExtractedMainContent,
    finding_id: str,
    title: str,
    severity: Severity,
    source: str,
    expected: str | int | float,
    observed: str | int | float,
    risk: str,
    recommendation: str,
    next_action: str,
    confidence: float,
) -> EntityReadinessFinding:
    return EntityReadinessFinding(
        id=finding_id,
        title=title,
        severity=severity,
        category=IssueCategory.ENTITY,
        page_url=page.page_url,
        evidence=[Evidence(source=source, selector=page.main_selector, expected=expected, observed=observed)],
        risk=risk,
        recommendation=recommendation,
        next_action=next_action,
        confidence=confidence,
    )


def _extract_structured_data_signal(soup: BeautifulSoup) -> EntityStructuredDataSignal:
    values: list[Any] = []
    for script in soup.find_all(
        "script",
        type=lambda value: bool(value)
        and str(value).lower().split(";", 1)[0].strip() == "application/ld+json",
    ):
        raw_json = script.string if script.string is not None else script.get_text()
        try:
            values.append(json.loads(raw_json))
        except json.JSONDecodeError:
            continue

    nodes = [node for value in values for node in _iter_nodes(value)]
    types = _unique([item for node in nodes for item in _types(node)])
    names = _unique([str(node["name"]).strip() for node in nodes if isinstance(node.get("name"), str) and node["name"].strip()])
    authors = _unique(_named_refs(nodes, "author"))
    publishers = _unique(_named_refs(nodes, "publisher"))
    same_as = _unique([url for node in nodes for url in _string_or_list(node.get("sameAs"))])

    return EntityStructuredDataSignal(
        types=types,
        names=names,
        authors=authors,
        publishers=publishers,
        same_as=same_as,
        has_organization="Organization" in types,
        has_person="Person" in types,
        has_article="Article" in types,
        has_web_page="WebPage" in types,
        has_breadcrumb_list="BreadcrumbList" in types,
    )


def _iter_nodes(value: Any):
    if isinstance(value, dict):
        yield value
        graph = value.get("@graph")
        if graph is not None:
            yield from _iter_nodes(graph)
        for item in value.values():
            if isinstance(item, (dict, list)):
                yield from _iter_nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_nodes(item)


def _types(node: dict[str, Any]) -> list[str]:
    value = node.get("@type")
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _named_refs(nodes: list[dict[str, Any]], key: str) -> list[str]:
    names: list[str] = []
    for node in nodes:
        value = node.get(key)
        if isinstance(value, dict):
            name = value.get("name")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
        elif isinstance(value, list):
            names.extend(_named_refs([{key: item} for item in value], key))
        elif isinstance(value, str) and value.strip():
            names.append(value.strip())
    return names


def _string_or_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _visible_cues(
    soup: BeautifulSoup,
    pattern: re.Pattern[str],
    selectors: list[str],
    meta_names: tuple[str, ...],
) -> list[str]:
    cues: list[str] = []
    for tag in soup.select(",".join(selectors)):
        text = _clean_text(tag.get_text(" "))
        if text:
            cues.append(text)
    for meta_name in meta_names:
        tag = soup.find("meta", attrs={"name": meta_name}) or soup.find("meta", property=meta_name)
        if tag and tag.get("content"):
            cues.append(str(tag["content"]).strip())
    for text in soup.find_all(string=pattern):
        cleaned = _clean_text(str(text))
        if cleaned:
            cues.append(cleaned)
    return _unique(cues)[:5]


def _build_summary(
    page_audits: list[EntityReadinessPageAudit],
    findings: list[EntityReadinessFinding],
) -> EntityReadinessSummary:
    by_severity = Counter(str(finding.severity) for finding in findings)
    by_category = Counter(str(finding.category) for finding in findings)
    scores = [_score_page(audit, findings) for audit in page_audits]
    return EntityReadinessSummary(
        total_pages=len(page_audits),
        findings_total=len(findings),
        by_severity=dict(sorted(by_severity.items())),
        by_category=dict(sorted(by_category.items())),
        pages_with_primary_entity=sum(1 for audit in page_audits if bool(audit.primary_entity)),
        pages_with_author_signal=sum(1 for audit in page_audits if bool(audit.visible_authorship_signals or audit.structured_data.authors or audit.structured_data.has_person)),
        pages_with_publisher_signal=sum(1 for audit in page_audits if bool(audit.visible_organization_signals or audit.structured_data.publishers or audit.structured_data.has_organization)),
        pages_with_same_as_signal=sum(1 for audit in page_audits if bool(audit.structured_data.same_as)),
        pages_with_article_schema=sum(1 for audit in page_audits if audit.structured_data.has_article),
        pages_with_web_page_schema=sum(1 for audit in page_audits if audit.structured_data.has_web_page),
        pages_with_breadcrumb_schema=sum(1 for audit in page_audits if audit.structured_data.has_breadcrumb_list),
        average_readiness_score=(sum(scores) / len(scores)) if scores else 0.0,
    )


def _score_page(audit: EntityReadinessPageAudit, findings: list[EntityReadinessFinding]) -> float:
    score = 100.0
    for finding in findings:
        if finding.page_url != audit.page_url:
            continue
        score -= {Severity.HIGH: 30, Severity.MEDIUM: 18, Severity.LOW: 8, Severity.INFO: 2}.get(finding.severity, 0)
    return max(0.0, score)


def _topic_terms(text: str) -> list[str]:
    counts = Counter(_tokens(text))
    return [term for term, _count in counts.most_common(8)]


def _tokens(text: str) -> list[str]:
    return [word for word in _WORD_RE.findall(text.lower()) if len(word) > 2 and word not in _STOPWORDS]


def _aligned(left: str, right: str) -> bool:
    left_tokens = set(_tokens(left))
    right_tokens = set(_tokens(right))
    if not left_tokens or not right_tokens:
        return False
    return bool(left_tokens & right_tokens)


def _overlap(left: str, right: str) -> float:
    left_tokens = set(_tokens(left))
    if not left_tokens:
        return 1.0
    right_tokens = set(_tokens(right))
    return len(left_tokens & right_tokens) / len(left_tokens)


def _alignment_summary(audit: EntityReadinessPageAudit) -> str:
    return (
        f"title_h1={audit.title_h1_aligned}; "
        f"meta_content={audit.meta_content_aligned}; "
        f"structured_data_content={audit.structured_data_content_aligned}"
    )


def _first_text(values: list[str]) -> str | None:
    return next((value for value in values if value.strip()), None)


def _clean_text(value: str) -> str:
    return " ".join(value.split()).strip()


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique
