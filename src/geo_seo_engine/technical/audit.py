from __future__ import annotations

from collections import Counter, defaultdict

from geo_seo_engine.core.models import Evidence, IssueCategory, Severity
from geo_seo_engine.inventory.models import InventoryResult, InventoryUrl
from geo_seo_engine.technical.models import (
    TechnicalAuditFinding,
    TechnicalAuditOptions,
    TechnicalAuditResult,
    TechnicalAuditSummary,
)


def run_technical_audit(
    inventory: InventoryResult,
    options: TechnicalAuditOptions | None = None,
) -> TechnicalAuditResult:
    audit_options = options or TechnicalAuditOptions()
    findings: list[TechnicalAuditFinding] = []

    for page in inventory.urls:
        if page.status_code != 200:
            findings.append(_status_not_200_finding(page))

        if page.has_error:
            findings.append(_fetch_error_finding(page))

        if audit_options.flag_non_html and not page.is_html:
            findings.append(_non_html_finding(page))

        if audit_options.flag_redirects and page.is_redirected:
            findings.append(_redirect_finding(page))

        if page.depth > audit_options.max_depth_warning:
            findings.append(_deep_page_finding(page, audit_options.max_depth_warning))

        if (
            audit_options.flag_zero_links
            and page.is_html
            and page.status_code == 200
            and not page.has_error
            and page.links_found == 0
        ):
            findings.append(_zero_links_finding(page))

    if inventory.summary.max_pages_reached:
        findings.append(_max_pages_reached_finding(inventory))

    skipped_count = inventory.summary.skipped_urls
    if skipped_count > audit_options.high_skipped_urls_warning:
        findings.append(
            _high_skipped_urls_finding(
                inventory,
                audit_options.high_skipped_urls_warning,
            )
        )

    findings.extend(_duplicate_final_url_findings(inventory.urls))

    return TechnicalAuditResult(
        start_url=inventory.start_url,
        findings=findings,
        summary=_build_summary(findings),
    )


def _status_not_200_finding(page: InventoryUrl) -> TechnicalAuditFinding:
    severity = (
        Severity.HIGH
        if page.status_code >= 400 or page.status_code == 0
        else Severity.MEDIUM
    )
    return TechnicalAuditFinding(
        id="technical.status_not_200",
        title="Fetched URL did not return HTTP 200",
        severity=severity,
        category=IssueCategory.CRAWLABILITY,
        url=page.url,
        evidence=[
            Evidence(
                source="inventory",
                value=page.status_code,
                expected=200,
                observed=page.status_code,
            ),
        ],
        risk=(
            "Important pages that do not return 200 can be harder to crawl, inspect, "
            "or use as stable landing pages."
        ),
        recommendation=(
            "Review why this URL returns a non-200 status and decide whether it should be "
            "fixed, redirected intentionally, or removed from internal discovery paths."
        ),
        next_action=f"Check server response and internal links for {page.url}.",
        confidence=1.0,
    )


def _fetch_error_finding(page: InventoryUrl) -> TechnicalAuditFinding:
    return TechnicalAuditFinding(
        id="technical.fetch_error",
        title="URL had a fetch error during crawl",
        severity=Severity.HIGH,
        category=IssueCategory.CRAWLABILITY,
        url=page.url,
        evidence=[
            Evidence(
                source="inventory",
                value=page.error or "fetch_error",
                observed=page.error or "fetch_error",
            ),
        ],
        risk=(
            "Crawler failures can hide page content and prevent the audit from validating "
            "technical signals on the affected URL."
        ),
        recommendation=(
            "Investigate connectivity, timeout, TLS, DNS, or application errors for the "
            "affected URL."
        ),
        next_action=(
            f"Re-run a targeted request for {page.url} and inspect the failure reason."
        ),
        confidence=1.0,
    )


def _non_html_finding(page: InventoryUrl) -> TechnicalAuditFinding:
    return TechnicalAuditFinding(
        id="technical.non_html_url",
        title="Discovered URL is not HTML",
        severity=Severity.LOW,
        category=IssueCategory.TECHNICAL,
        url=page.url,
        evidence=[
            Evidence(
                source="inventory",
                value=page.content_type or "unknown",
                expected="text/html",
                observed=page.content_type or "unknown",
            ),
        ],
        risk=(
            "Non-HTML URLs discovered in the crawl can dilute crawl budget analysis if they "
            "are not intentional content assets."
        ),
        recommendation=(
            "Confirm whether this URL should be linked from crawlable pages or excluded from "
            "the scoped crawl rules."
        ),
        next_action=(
            f"Classify {page.url} as an intentional asset or remove unnecessary internal "
            "links to it."
        ),
        confidence=0.95,
    )


def _redirect_finding(page: InventoryUrl) -> TechnicalAuditFinding:
    return TechnicalAuditFinding(
        id="technical.redirected_url",
        title="Discovered URL redirects to another URL",
        severity=Severity.LOW,
        category=IssueCategory.CRAWLABILITY,
        url=page.url,
        evidence=[
            Evidence(
                source="inventory",
                value=page.final_url,
                expected=page.normalized_url,
                observed=page.final_url,
            ),
        ],
        risk=(
            "Internal links to redirected URLs add avoidable hops and can make canonical URL "
            "signals less clear."
        ),
        recommendation=(
            "Update internal links to point directly to the final destination when the "
            "redirect is intentional."
        ),
        next_action=(
            f"Replace internal references to {page.normalized_url} with {page.final_url} "
            "where appropriate."
        ),
        confidence=1.0,
    )


def _deep_page_finding(page: InventoryUrl, max_depth_warning: int) -> TechnicalAuditFinding:
    return TechnicalAuditFinding(
        id="technical.deep_page",
        title="Page is deeper than the configured warning threshold",
        severity=Severity.MEDIUM,
        category=IssueCategory.CRAWLABILITY,
        url=page.url,
        evidence=[
            Evidence(
                source="inventory",
                value=page.depth,
                expected=max_depth_warning,
                observed=page.depth,
            ),
        ],
        risk="Deep pages may be harder for users and crawlers to discover from key entry points.",
        recommendation=(
            "Review navigation, hub pages, breadcrumbs, or contextual links to reduce the "
            "click depth for important pages."
        ),
        next_action=f"Decide whether {page.url} is important enough to receive stronger internal links.",
        confidence=0.9,
    )


def _zero_links_finding(page: InventoryUrl) -> TechnicalAuditFinding:
    return TechnicalAuditFinding(
        id="technical.zero_links_found",
        title="HTML page has zero links found",
        severity=Severity.MEDIUM,
        category=IssueCategory.CRAWLABILITY,
        url=page.url,
        evidence=[
            Evidence(
                source="inventory",
                value=page.links_found,
                expected="> 0",
                observed=page.links_found,
            ),
        ],
        risk=(
            "A page with no discovered links can behave like a dead end in the crawl and may "
            "not support discovery of related content."
        ),
        recommendation=(
            "Add useful navigation or contextual links when the page is meant to participate "
            "in the site structure."
        ),
        next_action=f"Inspect rendered links or HTML anchors on {page.url}.",
        confidence=0.9,
    )


def _max_pages_reached_finding(inventory: InventoryResult) -> TechnicalAuditFinding:
    return TechnicalAuditFinding(
        id="technical.max_pages_reached",
        title="Crawl stopped after reaching the max pages limit",
        severity=Severity.MEDIUM,
        category=IssueCategory.CRAWLABILITY,
        url=None,
        evidence=[
            Evidence(
                source="inventory.summary",
                value=True,
                expected=False,
                observed=inventory.summary.max_pages_reached,
            ),
            Evidence(
                source="inventory.summary",
                value=inventory.summary.total_pages,
                observed=inventory.summary.total_pages,
            ),
        ],
        risk=(
            "The audit may not represent the full scoped site because the crawl stopped at "
            "the configured page limit."
        ),
        recommendation=(
            "Increase the max pages limit or narrow crawl scope before treating the audit as "
            "complete."
        ),
        next_action=(
            "Re-run the crawl with a higher --max-pages value or tighter include/exclude "
            "patterns."
        ),
        confidence=1.0,
    )


def _high_skipped_urls_finding(inventory: InventoryResult, threshold: int) -> TechnicalAuditFinding:
    skipped_count = inventory.summary.skipped_urls
    return TechnicalAuditFinding(
        id="technical.high_skipped_urls",
        title="High number of skipped URLs",
        severity=Severity.MEDIUM,
        category=IssueCategory.CRAWLABILITY,
        url=None,
        evidence=[
            Evidence(
                source="inventory.summary",
                value=skipped_count,
                expected=threshold,
                observed=skipped_count,
            ),
        ],
        risk=(
            "Many skipped URLs can indicate noisy templates, external leakage, overly broad "
            "discovery, or crawl scope rules that need review."
        ),
        recommendation=(
            "Review skipped URL reasons and adjust internal links, allowed hosts, include "
            "patterns, or exclude patterns."
        ),
        next_action=(
            "Group skipped URLs by reason and update crawl scope or source templates "
            "accordingly."
        ),
        confidence=0.95,
    )


def _duplicate_final_url_findings(urls: list[InventoryUrl]) -> list[TechnicalAuditFinding]:
    by_final_url: dict[str, list[InventoryUrl]] = defaultdict(list)
    for page in urls:
        by_final_url[page.final_url].append(page)

    findings: list[TechnicalAuditFinding] = []
    for final_url, pages in sorted(by_final_url.items()):
        source_urls = sorted({page.normalized_url for page in pages})
        if len(source_urls) < 2:
            continue

        findings.append(
            TechnicalAuditFinding(
                id="technical.duplicate_final_url",
                title="Multiple discovered URLs resolve to the same final URL",
                severity=Severity.MEDIUM,
                category=IssueCategory.INDEXABILITY,
                url=final_url,
                evidence=[
                    Evidence(
                        source="inventory",
                        value=", ".join(source_urls),
                        expected="one source URL per final URL",
                        observed=final_url,
                    ),
                ],
                risk=(
                    "Multiple URL variants resolving to the same destination can make internal "
                    "linking and canonicalization signals less consistent."
                ),
                recommendation=(
                    "Standardize internal links on one preferred URL variant and keep redirects "
                    "only where they are needed for users or legacy URLs."
                ),
                next_action=(
                    f"Choose the preferred source URL for {final_url} and update duplicate "
                    "internal links."
                ),
                confidence=0.85,
            )
        )

    return findings


def _build_summary(findings: list[TechnicalAuditFinding]) -> TechnicalAuditSummary:
    by_severity = Counter(str(finding.severity) for finding in findings)
    by_category = Counter(str(finding.category) for finding in findings)

    return TechnicalAuditSummary(
        total_findings=len(findings),
        by_severity=dict(sorted(by_severity.items())),
        by_category=dict(sorted(by_category.items())),
    )
