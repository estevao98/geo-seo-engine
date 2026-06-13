from __future__ import annotations

from collections import Counter

from geo_seo_engine.core.models import Evidence, IssueCategory, Severity
from geo_seo_engine.i18n.models import (
    HreflangAuditFinding,
    HreflangAuditOptions,
    HreflangAuditResult,
    HreflangAuditSummary,
    HreflangLink,
    PageHreflangInventory,
    SkippedHreflangLink,
)


def run_hreflang_audit(
    pages: list[PageHreflangInventory],
    options: HreflangAuditOptions | None = None,
    start_url: str | None = None,
) -> HreflangAuditResult:
    audit_options = options or HreflangAuditOptions()
    findings: list[HreflangAuditFinding] = []
    crawled_pages = {page.page_url: page for page in pages}
    missing_reciprocal_count = 0

    for page in pages:
        for skipped in page.skipped_links:
            if audit_options.flag_missing_href and skipped.reason == "missing_href":
                findings.append(_missing_href_finding(skipped))
            if audit_options.flag_missing_hreflang and skipped.reason == "missing_hreflang":
                findings.append(_missing_hreflang_finding(skipped))

        if audit_options.flag_missing_self_reference and page.links and not _has_self_reference(page):
            findings.append(_missing_self_reference_finding(page))

        if audit_options.flag_duplicate_values:
            for hreflang, count in page.duplicates.items():
                findings.append(_duplicate_value_finding(page, hreflang, count))

        if audit_options.flag_missing_x_default and page.links and not any(link.is_x_default for link in page.links):
            findings.append(_missing_x_default_finding(page))

        for link in page.links:
            if audit_options.flag_invalid_hreflang and link.is_invalid_hreflang:
                findings.append(_invalid_hreflang_finding(link))
            if audit_options.flag_invalid_url and link.is_invalid_url:
                findings.append(_invalid_url_finding(link))
            if audit_options.flag_relative_url and link.is_relative and not link.is_invalid_url:
                findings.append(_relative_url_finding(link))
            if audit_options.flag_external_hosts and link.is_external:
                findings.append(_external_host_finding(link))
            if _should_flag_missing_reciprocal(link, page, crawled_pages, audit_options):
                findings.append(_missing_reciprocal_finding(link))
                missing_reciprocal_count += 1

    return HreflangAuditResult(
        start_url=start_url,
        pages=pages,
        findings=findings,
        summary=_build_summary(pages, findings, missing_reciprocal_count),
    )


def _missing_href_finding(skipped: SkippedHreflangLink) -> HreflangAuditFinding:
    return HreflangAuditFinding(
        id="hreflang.missing_href",
        title="Hreflang alternate is missing href",
        severity=Severity.MEDIUM,
        category=IssueCategory.TECHNICAL,
        page_url=skipped.page_url,
        hreflang=skipped.raw_hreflang,
        evidence=[_evidence("link[rel='alternate'][hreflang]", skipped.raw_href, "non-empty href", "missing")],
        risk="A hreflang annotation without a target URL cannot identify the localized alternate page.",
        recommendation="Add a fully qualified href URL for each hreflang alternate annotation.",
        next_action=f"Inspect alternate hreflang tags without href on {skipped.page_url}.",
        confidence=1.0,
    )


def _missing_hreflang_finding(skipped: SkippedHreflangLink) -> HreflangAuditFinding:
    return HreflangAuditFinding(
        id="hreflang.missing_hreflang",
        title="Alternate link is missing hreflang",
        severity=Severity.MEDIUM,
        category=IssueCategory.TECHNICAL,
        page_url=skipped.page_url,
        target_url=skipped.raw_href,
        evidence=[_evidence("link[rel='alternate'][href]", skipped.raw_hreflang, "non-empty hreflang", "missing")],
        risk="An alternate link without hreflang does not declare the language or locale of the target page.",
        recommendation="Add a valid hreflang value such as en, pt-BR, es-ES, or x-default.",
        next_action=f"Inspect alternate links without hreflang on {skipped.page_url}.",
        confidence=1.0,
    )


def _missing_self_reference_finding(page: PageHreflangInventory) -> HreflangAuditFinding:
    return HreflangAuditFinding(
        id="hreflang.missing_self_reference",
        title="Page is missing a self-referencing hreflang annotation",
        severity=Severity.MEDIUM,
        category=IssueCategory.TECHNICAL,
        page_url=page.page_url,
        evidence=[_evidence("html.head link[rel='alternate'][hreflang]", None, page.page_url, "no self-reference")],
        risk="Localized pages should list themselves and their alternates so crawlers can interpret the full cluster consistently.",
        recommendation="Add a hreflang entry whose href resolves to the current page URL.",
        next_action=f"Add or fix the self-referencing hreflang tag on {page.page_url}.",
        confidence=0.95,
    )


def _invalid_hreflang_finding(link: HreflangLink) -> HreflangAuditFinding:
    return HreflangAuditFinding(
        id="hreflang.invalid_hreflang",
        title="Hreflang value is invalid or suspicious",
        severity=Severity.MEDIUM,
        category=IssueCategory.TECHNICAL,
        page_url=link.page_url,
        hreflang=link.raw_hreflang,
        target_url=link.normalized_url,
        evidence=[_evidence("link[hreflang]", link.raw_hreflang, "language or language-region code", link.raw_hreflang)],
        risk="Invalid hreflang values can cause localized alternate annotations to be ignored.",
        recommendation="Use x-default, a language code like en, or a language-region code like pt-BR.",
        next_action=f"Replace hreflang={link.raw_hreflang!r} on {link.page_url} with a valid value.",
        confidence=0.95,
    )


def _invalid_url_finding(link: HreflangLink) -> HreflangAuditFinding:
    expected = "absolute HTTP(S) URL" if link.is_non_http else "valid HTTP(S) URL"
    return HreflangAuditFinding(
        id="hreflang.invalid_url",
        title="Hreflang alternate URL is invalid or unsupported",
        severity=Severity.MEDIUM,
        category=IssueCategory.TECHNICAL,
        page_url=link.page_url,
        hreflang=link.normalized_hreflang or link.raw_hreflang,
        target_url=link.resolved_url,
        evidence=[_evidence("link[rel='alternate'][href]", link.raw_href, expected, link.resolved_url)],
        risk="Invalid or non-HTTP(S) alternate URLs cannot be used as crawlable localized page targets.",
        recommendation="Use a valid fully qualified http or https URL for each alternate target.",
        next_action=f"Fix hreflang href={link.raw_href!r} on {link.page_url}.",
        confidence=0.95,
    )


def _relative_url_finding(link: HreflangLink) -> HreflangAuditFinding:
    return HreflangAuditFinding(
        id="hreflang.relative_url",
        title="Hreflang alternate uses a relative URL",
        severity=Severity.LOW,
        category=IssueCategory.TECHNICAL,
        page_url=link.page_url,
        hreflang=link.normalized_hreflang,
        target_url=link.normalized_url,
        evidence=[_evidence("link[rel='alternate'][href]", link.raw_href, "fully qualified URL", link.raw_href)],
        risk="Google recommends fully qualified alternate URLs; relative URLs are easier to misinterpret across environments.",
        recommendation="Replace relative alternate href values with absolute http or https URLs.",
        next_action=f"Change {link.raw_href!r} to {link.normalized_url!r} on {link.page_url}.",
        confidence=0.9,
    )


def _duplicate_value_finding(page: PageHreflangInventory, hreflang: str, count: int) -> HreflangAuditFinding:
    return HreflangAuditFinding(
        id="hreflang.duplicate_value",
        title="Page has duplicate hreflang values",
        severity=Severity.LOW,
        category=IssueCategory.TECHNICAL,
        page_url=page.page_url,
        hreflang=hreflang,
        evidence=[_evidence("link[rel='alternate'][hreflang]", hreflang, "one target per hreflang value", count)],
        risk="Duplicate hreflang values on a page can make the intended locale target ambiguous.",
        recommendation="Keep one canonical alternate URL per hreflang value on each page.",
        next_action=f"Deduplicate hreflang={hreflang!r} annotations on {page.page_url}.",
        confidence=0.95,
    )


def _external_host_finding(link: HreflangLink) -> HreflangAuditFinding:
    return HreflangAuditFinding(
        id="hreflang.external_host",
        title="Hreflang alternate points outside the configured hosts",
        severity=Severity.INFO,
        category=IssueCategory.TECHNICAL,
        page_url=link.page_url,
        hreflang=link.normalized_hreflang,
        target_url=link.normalized_url,
        evidence=[_evidence("link[rel='alternate'][href]", link.normalized_url, "configured allowed hosts", link.normalized_url)],
        risk="External alternate hosts can be intentional for international sites, but they are outside this crawl scope.",
        recommendation="Confirm the external localized host is owned, crawlable, and part of the intended hreflang cluster.",
        next_action=f"Validate ownership and reciprocal hreflang coverage for {link.normalized_url}.",
        confidence=0.9,
    )


def _missing_reciprocal_finding(link: HreflangLink) -> HreflangAuditFinding:
    return HreflangAuditFinding(
        id="hreflang.missing_reciprocal",
        title="Crawled hreflang target does not link back reciprocally",
        severity=Severity.MEDIUM,
        category=IssueCategory.TECHNICAL,
        page_url=link.page_url,
        hreflang=link.normalized_hreflang,
        target_url=link.normalized_url,
        evidence=[_evidence("crawled hreflang cluster", link.normalized_url, f"reciprocal link to {link.page_url}", "missing")],
        risk="Missing bidirectional hreflang references can prevent crawlers from trusting the localized page cluster.",
        recommendation="Ensure every crawled localized target links back to the source page with the appropriate hreflang annotation.",
        next_action=f"Add a reciprocal hreflang link from {link.normalized_url} back to {link.page_url}.",
        confidence=0.9,
    )


def _missing_x_default_finding(page: PageHreflangInventory) -> HreflangAuditFinding:
    return HreflangAuditFinding(
        id="hreflang.missing_x_default",
        title="Page has no x-default hreflang annotation",
        severity=Severity.INFO,
        category=IssueCategory.TECHNICAL,
        page_url=page.page_url,
        evidence=[_evidence("link[rel='alternate'][hreflang='x-default']", None, "optional x-default", "missing")],
        risk="x-default is optional, but can clarify the default page for unmatched languages or selectors.",
        recommendation="Consider adding x-default when the site has a global default, selector, or fallback URL.",
        next_action=f"Decide whether {page.page_url} needs an x-default alternate.",
        confidence=0.7,
    )


def _has_self_reference(page: PageHreflangInventory) -> bool:
    return any(link.is_self_reference and not link.is_invalid_hreflang for link in page.links)


def _should_flag_missing_reciprocal(
    link: HreflangLink,
    page: PageHreflangInventory,
    crawled_pages: dict[str, PageHreflangInventory],
    options: HreflangAuditOptions,
) -> bool:
    if not options.flag_missing_reciprocal or link.is_self_reference or link.is_invalid_url or link.is_invalid_hreflang:
        return False
    target_page = crawled_pages.get(link.normalized_url)
    if target_page is None:
        return False
    return not any(
        target_link.normalized_url == page.page_url
        and not target_link.is_invalid_url
        and not target_link.is_invalid_hreflang
        for target_link in target_page.links
    )


def _build_summary(
    pages: list[PageHreflangInventory],
    findings: list[HreflangAuditFinding],
    missing_reciprocal_count: int,
) -> HreflangAuditSummary:
    links = [link for page in pages for link in page.links]
    by_severity = Counter(str(finding.severity) for finding in findings)
    by_category = Counter(str(finding.category) for finding in findings)

    return HreflangAuditSummary(
        total_pages=len(pages),
        total_links=len(links),
        findings_total=len(findings),
        by_severity=dict(sorted(by_severity.items())),
        by_category=dict(sorted(by_category.items())),
        pages_missing_self_reference=sum(1 for page in pages if page.links and not _has_self_reference(page)),
        pages_with_x_default=sum(1 for page in pages if any(link.is_x_default for link in page.links)),
        duplicate_hreflang_pages=sum(1 for page in pages if page.duplicates),
        invalid_hreflang_links=sum(1 for link in links if link.is_invalid_hreflang),
        invalid_url_links=sum(1 for link in links if link.is_invalid_url),
        relative_url_links=sum(1 for link in links if link.is_relative),
        external_url_links=sum(1 for link in links if link.is_external),
        missing_reciprocal_links=missing_reciprocal_count,
    )


def _evidence(selector: str, value, expected, observed) -> Evidence:
    return Evidence(
        source="html.head",
        selector=selector,
        value=value,
        expected=expected,
        observed=observed,
    )
