from __future__ import annotations

from collections import Counter

from geo_seo_engine.core.models import Evidence, IssueCategory, Severity
from geo_seo_engine.rendering.models import (
    PageRenderSnapshot,
    RenderingAuditFinding,
    RenderingAuditOptions,
    RenderingAuditResult,
    RenderingAuditSummary,
)


def run_rendering_audit(
    pages: list[PageRenderSnapshot],
    options: RenderingAuditOptions | None = None,
    start_url: str | None = None,
) -> RenderingAuditResult:
    audit_options = options or RenderingAuditOptions()
    findings: list[RenderingAuditFinding] = []

    for page in pages:
        if page.render_status in {"error", "timeout", "skipped"} or page.render_error:
            findings.append(_render_error_finding(page))
            continue

        if audit_options.flag_title_changed and _changed(page.static_title, page.rendered_title):
            findings.append(_changed_finding(page, "title", page.static_title, page.rendered_title, Severity.LOW))
        if audit_options.flag_meta_description_changed and _changed(
            page.static_meta_description,
            page.rendered_meta_description,
        ):
            findings.append(
                _changed_finding(
                    page,
                    "meta_description",
                    page.static_meta_description,
                    page.rendered_meta_description,
                    Severity.LOW,
                )
            )
        if audit_options.flag_canonical_changed and _changed(page.static_canonical, page.rendered_canonical):
            findings.append(
                _changed_finding(page, "canonical", page.static_canonical, page.rendered_canonical, Severity.MEDIUM)
            )
        if audit_options.flag_robots_changed and _changed(page.static_robots, page.rendered_robots):
            severity = Severity.HIGH if _has_noindex(page.rendered_robots) else Severity.MEDIUM
            findings.append(_changed_finding(page, "robots", page.static_robots, page.rendered_robots, severity))
        if audit_options.flag_rendered_noindex and not _has_noindex(page.static_robots) and _has_noindex(page.rendered_robots):
            findings.append(_rendered_noindex_finding(page))
        if audit_options.flag_links_added_by_js:
            added_links = sorted(set(page.rendered_links) - set(page.static_links))
            if _links_added_exceeds_threshold(page, added_links, audit_options):
                findings.append(_links_added_finding(page, added_links))
        if _static_sparse_rendered_populated(page, audit_options):
            if audit_options.flag_static_content_sparse:
                findings.append(_static_sparse_finding(page))
            if audit_options.flag_content_only_after_render and page.static_text_length == 0:
                findings.append(_content_only_after_render_finding(page))

    return RenderingAuditResult(
        start_url=start_url,
        pages=pages,
        findings=findings,
        summary=_build_summary(pages, findings),
    )


def _changed(static_value: str | None, rendered_value: str | None) -> bool:
    return (static_value or "").strip() != (rendered_value or "").strip()


def _has_noindex(value: str | None) -> bool:
    return "noindex" in {part.strip().lower() for part in (value or "").split(",")}


def _links_added_exceeds_threshold(
    page: PageRenderSnapshot,
    added_links: list[str],
    options: RenderingAuditOptions,
) -> bool:
    if len(added_links) < options.min_added_links_warning:
        return False
    static_count = max(len(page.static_links), 1)
    return (len(added_links) / static_count) >= options.link_added_ratio_warning


def _static_sparse_rendered_populated(page: PageRenderSnapshot, options: RenderingAuditOptions) -> bool:
    return (
        page.static_text_length <= options.static_sparse_text_threshold
        and page.rendered_text_length >= options.rendered_populated_text_threshold
    )


def _changed_finding(
    page: PageRenderSnapshot,
    field_name: str,
    static_value: str | None,
    rendered_value: str | None,
    severity: Severity,
) -> RenderingAuditFinding:
    titles = {
        "title": "HTML title changes after rendering",
        "meta_description": "Meta description changes after rendering",
        "canonical": "Canonical URL changes after rendering",
        "robots": "Robots meta changes after rendering",
    }
    return RenderingAuditFinding(
        id=f"rendering.{field_name}_changed",
        title=titles[field_name],
        severity=severity,
        category=IssueCategory.INDEXABILITY if field_name in {"canonical", "robots"} else IssueCategory.CONTENT,
        page_url=page.page_url,
        evidence=[
            Evidence(
                source="rendering.compare",
                selector=field_name,
                value=rendered_value,
                expected=static_value or "same as static HTML",
                observed=rendered_value or "missing after render",
            )
        ],
        risk="Bots and parsers that do not execute JavaScript may see different SEO signals than rendered users or Google rendering.",
        recommendation="Prefer stable critical SEO tags in the initial HTML response, or verify that the change is intentional and supported for target crawlers.",
        next_action=f"Compare static and rendered {field_name} on {page.page_url}.",
        confidence=0.9,
    )


def _render_error_finding(page: PageRenderSnapshot) -> RenderingAuditFinding:
    return RenderingAuditFinding(
        id="rendering.render_error",
        title="Page could not be rendered",
        severity=Severity.MEDIUM,
        category=IssueCategory.TECHNICAL,
        page_url=page.page_url,
        evidence=[
            Evidence(
                source="renderer",
                value=page.render_status,
                expected="rendered",
                observed=page.render_error or page.render_status,
            )
        ],
        risk="Rendering failures can hide JavaScript-dependent SEO signals and content from this audit layer.",
        recommendation="Investigate renderer configuration, page runtime errors, timeout limits, or test with a browser-backed renderer outside the default static pipeline.",
        next_action=f"Re-run rendering for {page.page_url} with a configured renderer and capture the error details.",
        confidence=0.95,
    )


def _rendered_noindex_finding(page: PageRenderSnapshot) -> RenderingAuditFinding:
    return RenderingAuditFinding(
        id="rendering.rendered_noindex",
        title="Rendered robots meta adds noindex",
        severity=Severity.HIGH,
        category=IssueCategory.INDEXABILITY,
        page_url=page.page_url,
        evidence=[
            Evidence(
                source="rendering.compare",
                selector="meta[name='robots']",
                value=page.rendered_robots,
                expected="no rendered noindex unless intentional",
                observed=page.rendered_robots,
            )
        ],
        risk="A rendered noindex directive can prevent indexing if Google processes the JavaScript-mutated robots tag.",
        recommendation="Keep indexability directives stable and explicit in the initial HTML unless the rendered noindex is intentional.",
        next_action=f"Confirm whether rendered noindex is expected on {page.page_url}.",
        confidence=0.95,
    )


def _links_added_finding(page: PageRenderSnapshot, added_links: list[str]) -> RenderingAuditFinding:
    preview = added_links[:10]
    return RenderingAuditFinding(
        id="rendering.links_added_by_js",
        title="JavaScript adds crawlable links after rendering",
        severity=Severity.MEDIUM if len(added_links) >= 10 else Severity.LOW,
        category=IssueCategory.CRAWLABILITY,
        page_url=page.page_url,
        evidence=[
            Evidence(
                source="rendering.links",
                selector="a[href]",
                value=" | ".join(preview),
                expected="important internal links available in static HTML",
                observed=f"{len(added_links)} links only found after render",
            )
        ],
        risk="Crawlers that do not render JavaScript may miss important discovery paths.",
        recommendation="Expose important navigation and internal links in server-rendered or pre-rendered HTML where possible.",
        next_action=f"Review whether JS-only links on {page.page_url} are critical for discovery.",
        confidence=0.85,
    )


def _static_sparse_finding(page: PageRenderSnapshot) -> RenderingAuditFinding:
    return RenderingAuditFinding(
        id="rendering.static_content_sparse",
        title="Static HTML is sparse but rendered content is populated",
        severity=Severity.MEDIUM,
        category=IssueCategory.CONTENT,
        page_url=page.page_url,
        evidence=[
            Evidence(
                source="rendering.text",
                value=page.rendered_text_length,
                expected="substantial primary content in static HTML",
                observed=f"static_text_length={page.static_text_length}, rendered_text_length={page.rendered_text_length}",
            )
        ],
        risk="Content that depends on rendering can be slower for users and unavailable to bots that do not execute JavaScript.",
        recommendation="Consider server-side rendering, static generation, or pre-rendering for primary content.",
        next_action=f"Inspect app-shell or client-only content patterns on {page.page_url}.",
        confidence=0.85,
    )


def _content_only_after_render_finding(page: PageRenderSnapshot) -> RenderingAuditFinding:
    return RenderingAuditFinding(
        id="rendering.content_only_after_render",
        title="Visible content appears only after rendering",
        severity=Severity.MEDIUM,
        category=IssueCategory.CONTENT,
        page_url=page.page_url,
        evidence=[
            Evidence(
                source="rendering.text",
                value=page.rendered_text_length,
                expected="some visible content in static HTML",
                observed="static HTML text length is zero",
            )
        ],
        risk="A client-only app shell may provide little useful content to non-rendering bots and parsers.",
        recommendation="Provide meaningful initial HTML for primary page content and critical SEO signals.",
        next_action=f"Check whether {page.page_url} is an app shell that requires JavaScript for all content.",
        confidence=0.9,
    )


def _build_summary(
    pages: list[PageRenderSnapshot],
    findings: list[RenderingAuditFinding],
) -> RenderingAuditSummary:
    by_severity = Counter(str(finding.severity) for finding in findings)
    by_category = Counter(str(finding.category) for finding in findings)
    finding_pages = _pages_by_finding(findings)

    return RenderingAuditSummary(
        total_pages=len(pages),
        rendered_pages=sum(1 for page in pages if page.render_status == "rendered" and not page.render_error),
        render_errors=sum(1 for page in pages if page.render_status in {"error", "timeout", "skipped"} or page.render_error),
        findings_total=len(findings),
        by_severity=dict(sorted(by_severity.items())),
        by_category=dict(sorted(by_category.items())),
        pages_title_changed=len(finding_pages.get("rendering.title_changed", set())),
        pages_description_changed=len(finding_pages.get("rendering.meta_description_changed", set())),
        pages_canonical_changed=len(finding_pages.get("rendering.canonical_changed", set())),
        pages_robots_changed=len(finding_pages.get("rendering.robots_changed", set())),
        pages_links_added_by_js=len(finding_pages.get("rendering.links_added_by_js", set())),
        pages_static_sparse_rendered_content=len(finding_pages.get("rendering.static_content_sparse", set())),
    )


def _pages_by_finding(findings: list[RenderingAuditFinding]) -> dict[str, set[str]]:
    pages: dict[str, set[str]] = {}
    for finding in findings:
        pages.setdefault(finding.id, set()).add(finding.page_url)
    return pages
