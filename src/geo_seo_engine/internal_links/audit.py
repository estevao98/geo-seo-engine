from __future__ import annotations

from collections import Counter, defaultdict, deque

from geo_seo_engine.core import normalize_url
from geo_seo_engine.core.models import Evidence, IssueCategory, Severity
from geo_seo_engine.crawler import CrawlResult
from geo_seo_engine.internal_links.models import (
    InternalLinkEdge,
    InternalLinkGraphAuditResult,
    InternalLinkGraphFinding,
    InternalLinkGraphOptions,
    InternalLinkGraphSummary,
    InternalLinkPageMetrics,
)


def run_internal_link_graph_audit(
    crawl_result: CrawlResult,
    options: InternalLinkGraphOptions | None = None,
) -> InternalLinkGraphAuditResult:
    audit_options = options or InternalLinkGraphOptions()
    pages_by_url = {page.normalized_url: page for page in crawl_result.pages}
    start_url = crawl_result.start_url
    reachable_depths = _reachable_depths(start_url, crawl_result.discovered_urls, pages_by_url)
    edges = []
    for link in crawl_result.discovered_urls:
        source_url = _normalize_or_original(link.source_url)
        edges.append(
            InternalLinkEdge(
                source_url=source_url,
                target_url=link.normalized_url,
                anchor_text=_clean_anchor(link.anchor_text),
                source_depth=max(link.depth - 1, 0),
                target_crawled=link.normalized_url in pages_by_url,
            )
        )

    inbound: dict[str, list[InternalLinkEdge]] = defaultdict(list)
    outbound: dict[str, list[InternalLinkEdge]] = defaultdict(list)
    for edge in edges:
        inbound[edge.target_url].append(edge)
        outbound[edge.source_url].append(edge)

    page_metrics = [
        _page_metrics(page_url, page, start_url, reachable_depths, inbound, outbound, audit_options)
        for page_url, page in sorted(pages_by_url.items())
    ]
    findings = _build_findings(page_metrics, edges, audit_options)

    return InternalLinkGraphAuditResult(
        start_url=start_url,
        pages=page_metrics,
        edges=edges,
        findings=findings,
        summary=_build_summary(crawl_result, page_metrics, edges, findings, audit_options),
    )


def _page_metrics(
    page_url: str,
    page,
    start_url: str,
    reachable_depths: dict[str, int],
    inbound: dict[str, list[InternalLinkEdge]],
    outbound: dict[str, list[InternalLinkEdge]],
    options: InternalLinkGraphOptions,
) -> InternalLinkPageMetrics:
    inbound_edges = inbound[page_url]
    outbound_edges = outbound[page_url]
    inbound_sources = {edge.source_url for edge in inbound_edges}
    outbound_targets = {edge.target_url for edge in outbound_edges}
    inbound_anchors = sorted({edge.anchor_text for edge in inbound_edges if edge.anchor_text})
    outbound_anchors = sorted({edge.anchor_text for edge in outbound_edges if edge.anchor_text})
    is_start_url = page_url == start_url
    inbound_count = len(inbound_edges)
    outbound_count = len(outbound_edges)
    is_orphan = not is_start_url and inbound_count == 0
    is_near_orphan = not is_start_url and not is_orphan and inbound_count <= options.near_orphan_inbound_threshold
    is_leaf = outbound_count == 0
    return InternalLinkPageMetrics(
        url=page.url,
        normalized_url=page_url,
        final_url=page.final_url,
        status_code=page.status_code,
        depth=reachable_depths.get(page_url, page.depth),
        discovered_from=page.discovered_from,
        inbound_internal_links=inbound_count,
        outbound_internal_links=outbound_count,
        unique_inbound_sources=len(inbound_sources),
        unique_outbound_targets=len(outbound_targets),
        inbound_anchor_texts=inbound_anchors,
        outbound_anchor_texts=outbound_anchors,
        is_start_url=is_start_url,
        is_orphan=is_orphan,
        is_near_orphan=is_near_orphan,
        is_leaf=is_leaf,
        is_hub=outbound_count >= options.hub_outbound_threshold,
        is_weakly_connected=not is_start_url and inbound_count <= 1 and outbound_count <= 1,
        has_extracted_content=page.main_content is not None,
    )


def _build_findings(
    pages: list[InternalLinkPageMetrics],
    edges: list[InternalLinkEdge],
    options: InternalLinkGraphOptions,
) -> list[InternalLinkGraphFinding]:
    findings: list[InternalLinkGraphFinding] = []
    generic_anchors = {_normalize_anchor(anchor) for anchor in options.generic_anchor_texts}

    for page in pages:
        if page.is_orphan:
            findings.append(
                _page_finding(
                    "internal_links.orphan_page",
                    "Page has no inbound internal links in the analyzed set",
                    Severity.HIGH,
                    page,
                    "inbound internal links",
                    ">= 1",
                    page.inbound_internal_links,
                    "Orphan pages may be hard for crawlers and users to discover through the site's own navigation paths.",
                    "Add relevant internal links from crawlable hub, category or related content pages.",
                    f"Choose at least one relevant source page and link to {page.normalized_url}.",
                )
            )
        elif page.is_near_orphan:
            findings.append(
                _page_finding(
                    "internal_links.near_orphan_page",
                    "Page has very few inbound internal links",
                    Severity.MEDIUM,
                    page,
                    "inbound internal links",
                    f"> {options.near_orphan_inbound_threshold}",
                    page.inbound_internal_links,
                    "Pages with very few internal entry points can be fragile if one template or link changes.",
                    "Add contextual links from additional relevant pages where they help users continue their task.",
                    f"Review internal link opportunities pointing to {page.normalized_url}.",
                )
            )

        if page.is_weakly_connected:
            findings.append(
                _page_finding(
                    "internal_links.weakly_connected_page",
                    "Page is weakly connected in the internal graph",
                    Severity.MEDIUM if page.is_leaf else Severity.LOW,
                    page,
                    "inbound/outbound internal links",
                    "more than one useful connection",
                    f"in={page.inbound_internal_links}; out={page.outbound_internal_links}",
                    "Weakly connected pages can become dead ends or isolated nodes in the site's information architecture.",
                    "Add useful inbound and outbound contextual links that reflect the page's role in the topic cluster.",
                    f"Map {page.normalized_url} to a parent, sibling or next-step page.",
                )
            )

        if page.depth > options.overly_deep_threshold:
            findings.append(
                _page_finding(
                    "internal_links.overly_deep_page",
                    "Page is deeper than the configured crawl-depth threshold",
                    Severity.MEDIUM,
                    page,
                    "reachable depth",
                    f"<= {options.overly_deep_threshold}",
                    page.depth,
                    "Important pages buried deep in the click path can be harder for users and crawlers to reach.",
                    "Expose important deep pages through relevant hubs, navigation or related-content links.",
                    f"Review whether {page.normalized_url} should be reachable in fewer clicks.",
                )
            )

        if page.inbound_internal_links > 0 and page.inbound_internal_links > len(
            page.inbound_anchor_texts
        ):
            findings.append(
                _page_finding(
                    "internal_links.weak_anchor_coverage",
                    "Inbound internal links have weak anchor text coverage",
                    Severity.LOW,
                    page,
                    "inbound anchor text",
                    "descriptive text on each inbound link",
                    f"{len(page.inbound_anchor_texts)} unique anchors for {page.inbound_internal_links} inbound links",
                    "Missing or empty anchor text removes context that helps users and crawlers understand why the target is relevant.",
                    "Use concise, descriptive anchor text for important internal links.",
                    f"Review anchors used to link to {page.normalized_url}.",
                )
            )
        elif (
            page.inbound_internal_links >= options.weak_anchor_diversity_threshold
            and len(page.inbound_anchor_texts) < options.weak_anchor_diversity_threshold
        ):
            findings.append(
                _page_finding(
                    "internal_links.low_anchor_diversity",
                    "Inbound anchor text has low diversity",
                    Severity.LOW,
                    page,
                    "unique inbound anchors",
                    f">= {options.weak_anchor_diversity_threshold}",
                    len(page.inbound_anchor_texts),
                    "Overly uniform anchors can make internal context less useful across different source pages.",
                    "Vary anchors naturally when the source-page context differs, without forcing keyword stuffing.",
                    f"Review repeated inbound anchors for {page.normalized_url}.",
                )
            )

    for edge in edges:
        if edge.anchor_text and _normalize_anchor(edge.anchor_text) in generic_anchors:
            findings.append(
                InternalLinkGraphFinding(
                    id="internal_links.generic_anchor_text",
                    title="Internal link uses generic anchor text",
                    severity=Severity.LOW,
                    category=IssueCategory.CRAWLABILITY,
                    page_url=edge.source_url,
                    evidence=[
                        Evidence(
                            source="internal_link.anchor_text",
                            value=edge.anchor_text,
                            expected="descriptive anchor",
                            observed=edge.target_url,
                        )
                    ],
                    risk="Generic anchors provide weak context about the destination page.",
                    recommendation="Replace generic anchors with concise text that describes the destination when it helps users.",
                    next_action=(
                        f"Rewrite the anchor from {edge.source_url} to {edge.target_url} "
                        "if the surrounding copy is not descriptive."
                    ),
                    confidence=0.9,
                )
            )

    for anchor, targets in sorted(_anchor_targets(edges).items()):
        if anchor and len(targets) >= options.repeated_anchor_target_threshold:
            findings.append(
                InternalLinkGraphFinding(
                    id="internal_links.repeated_anchor_multiple_targets",
                    title="Same anchor text points to multiple internal destinations",
                    severity=Severity.LOW,
                    category=IssueCategory.CRAWLABILITY,
                    page_url=None,
                    evidence=[
                        Evidence(
                            source="internal_link.anchor_text",
                            value=anchor,
                            expected="one clear destination intent",
                            observed=len(targets),
                        )
                    ],
                    risk="The same repeated anchor for different targets can blur destination intent and reduce link-context clarity.",
                    recommendation="Use more specific anchors when different destination pages serve different intents.",
                    next_action=f"Review destinations using the anchor text {anchor!r}.",
                    confidence=0.85,
                )
            )

    return findings


def _build_summary(
    crawl_result: CrawlResult,
    pages: list[InternalLinkPageMetrics],
    edges: list[InternalLinkEdge],
    findings: list[InternalLinkGraphFinding],
    options: InternalLinkGraphOptions,
) -> InternalLinkGraphSummary:
    by_severity = Counter(str(finding.severity) for finding in findings)
    by_category = Counter(str(finding.category) for finding in findings)
    crawled_urls = {page.normalized_url for page in pages}
    discovered_urls = {link.normalized_url for link in crawl_result.discovered_urls}
    generic_anchors = {_normalize_anchor(anchor) for anchor in options.generic_anchor_texts}
    repeated_anchors = {
        anchor: len(targets)
        for anchor, targets in sorted(_anchor_targets(edges).items())
        if anchor and len(targets) > 1
    }

    return InternalLinkGraphSummary(
        total_pages=len(pages),
        crawled_pages=len(crawl_result.pages),
        discovered_urls=len(discovered_urls),
        extracted_content_pages=sum(1 for page in pages if page.has_extracted_content),
        internal_edges=len(edges),
        discovered_not_crawled_count=len(discovered_urls - crawled_urls),
        crawled_not_discovered_count=len(
            {page.normalized_url for page in pages if not page.is_start_url} - discovered_urls
        ),
        orphan_pages=sum(1 for page in pages if page.is_orphan),
        near_orphan_pages=sum(1 for page in pages if page.is_near_orphan),
        leaf_pages=sum(1 for page in pages if page.is_leaf),
        hub_pages=sum(1 for page in pages if page.is_hub),
        weakly_connected_pages=sum(1 for page in pages if page.is_weakly_connected),
        max_depth=max((page.depth for page in pages), default=0),
        overly_deep_pages=sum(1 for page in pages if page.depth > options.overly_deep_threshold),
        generic_anchor_count=sum(
            1
            for edge in edges
            if _normalize_anchor(edge.anchor_text or "") in generic_anchors
        ),
        missing_anchor_count=sum(1 for edge in edges if not edge.anchor_text),
        repeated_anchor_texts=repeated_anchors,
        findings_total=len(findings),
        by_severity=dict(sorted(by_severity.items())),
        by_category=dict(sorted(by_category.items())),
    )


def _reachable_depths(start_url: str, links, pages_by_url: dict[str, object]) -> dict[str, int]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for link in links:
        source_url = _normalize_or_original(link.source_url)
        if source_url in pages_by_url and link.normalized_url in pages_by_url:
            adjacency[source_url].add(link.normalized_url)

    depths = {start_url: 0}
    queue = deque([start_url])
    while queue:
        current = queue.popleft()
        for target in sorted(adjacency[current]):
            if target not in depths:
                depths[target] = depths[current] + 1
                queue.append(target)
    return depths


def _page_finding(
    finding_id: str,
    title: str,
    severity: Severity,
    page: InternalLinkPageMetrics,
    evidence_source: str,
    expected: str | int,
    observed: str | int,
    risk: str,
    recommendation: str,
    next_action: str,
) -> InternalLinkGraphFinding:
    return InternalLinkGraphFinding(
        id=finding_id,
        title=title,
        severity=severity,
        category=IssueCategory.CRAWLABILITY,
        page_url=page.normalized_url,
        evidence=[Evidence(source=evidence_source, value=observed, expected=expected, observed=observed)],
        risk=risk,
        recommendation=recommendation,
        next_action=next_action,
        confidence=0.9,
    )


def _anchor_targets(edges: list[InternalLinkEdge]) -> dict[str, set[str]]:
    targets: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        anchor = _normalize_anchor(edge.anchor_text or "")
        if anchor:
            targets[anchor].add(edge.target_url)
    return targets


def _clean_anchor(anchor_text: str | None) -> str | None:
    if not anchor_text:
        return None
    cleaned = " ".join(anchor_text.split())
    return cleaned or None


def _normalize_anchor(anchor_text: str) -> str:
    return " ".join(anchor_text.lower().split())


def _normalize_or_original(url: str) -> str:
    try:
        return normalize_url(url).normalized_url
    except ValueError:
        return url
