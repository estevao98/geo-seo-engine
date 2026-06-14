from __future__ import annotations

import re
from collections import Counter

from geo_seo_engine.content import ExtractedMainContent
from geo_seo_engine.content_quality.models import (
    ContentQualityAuditOptions,
    ContentQualityAuditResult,
    ContentQualityFinding,
    ContentQualitySummary,
)
from geo_seo_engine.core.models import Evidence, IssueCategory, Severity

_WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def run_content_quality_audit(
    pages: list[ExtractedMainContent],
    options: ContentQualityAuditOptions | None = None,
    start_url: str | None = None,
) -> ContentQualityAuditResult:
    audit_options = options or ContentQualityAuditOptions()
    findings: list[ContentQualityFinding] = []

    for page in pages:
        findings.extend(_findings_for_page(page, audit_options))

    return ContentQualityAuditResult(
        start_url=start_url,
        pages=pages,
        findings=findings,
        summary=_build_summary(pages, findings, audit_options),
    )


def _findings_for_page(
    page: ExtractedMainContent,
    options: ContentQualityAuditOptions,
) -> list[ContentQualityFinding]:
    findings: list[ContentQualityFinding] = []
    h1_headings = [heading for heading in page.headings if heading.level == 1]

    if page.word_count == 0 or not page.plain_text.strip():
        findings.append(
            _finding(
                page,
                "content.missing_main_content",
                "Main content is missing",
                Severity.HIGH,
                "main content",
                "present",
                "missing",
                "A page without extractable main content gives users and search systems little page-specific information.",
                "Add crawlable, page-specific main content or fix the template so the main content is available in HTML.",
                f"Inspect main content extraction for {page.page_url}.",
                1.0,
            )
        )
    elif page.word_count < options.thin_content_word_threshold:
        findings.append(
            _finding(
                page,
                "content.thin_content",
                "Main content has a very low word count",
                Severity.MEDIUM,
                "word count",
                f">= {options.thin_content_word_threshold}",
                page.word_count,
                "Very short body copy may not answer the page intent with enough useful detail.",
                "Expand the page with original, user-focused information where the intent requires it.",
                f"Review whether {page.page_url} satisfies its search intent.",
                0.9,
            )
        )

    if not h1_headings:
        findings.append(
            _finding(
                page,
                "content.missing_h1",
                "Page is missing an H1 in main content",
                Severity.MEDIUM,
                "main content headings",
                "one H1",
                "missing",
                "A missing H1 can make the primary page topic less clear in the extracted content structure.",
                "Add one descriptive H1 that reflects the main purpose of the page.",
                f"Add or expose a primary H1 on {page.page_url}.",
                0.95,
            )
        )
    elif len(h1_headings) > 1:
        findings.append(
            _finding(
                page,
                "content.multiple_h1",
                "Page has multiple H1 headings in main content",
                Severity.LOW,
                "main content headings",
                "one H1",
                len(h1_headings),
                "Multiple H1s can make the primary topic hierarchy ambiguous.",
                "Use one primary H1 and demote secondary section titles to H2 or lower where appropriate.",
                f"Review H1 usage on {page.page_url}.",
                0.9,
            )
        )

    if options.flag_weak_heading_structure and _has_weak_heading_structure(page):
        findings.append(
            _finding(
                page,
                "content.weak_heading_structure",
                "Heading structure is weak or skipped",
                Severity.LOW,
                "main content headings",
                "ordered H1-H3 hierarchy",
                _heading_sequence(page),
                "Skipped or out-of-order headings can make long-form content harder to scan and interpret.",
                "Use a clear heading hierarchy that starts with the primary topic and groups sections predictably.",
                f"Review heading order on {page.page_url}.",
                0.8,
            )
        )

    if not _has_text(page.title):
        findings.append(
            _finding(
                page,
                "content.missing_title",
                "Page title is missing",
                Severity.HIGH,
                "html title",
                "non-empty title",
                "missing",
                "Missing title text can reduce clarity in browser tabs, search results and shared page previews.",
                "Add a concise, descriptive title element for the page.",
                f"Add a title element on {page.page_url}.",
                1.0,
            )
        )

    if not _has_text(page.meta_description):
        findings.append(
            _finding(
                page,
                "content.missing_meta_description",
                "Meta description is missing",
                Severity.LOW,
                "meta description",
                "non-empty description",
                "missing",
                "A missing meta description can reduce control over page summaries in search experiences.",
                "Add a concise description that accurately summarizes the page content.",
                f"Write a meta description for {page.page_url}.",
                0.95,
            )
        )

    if options.flag_title_h1_mismatch and page.title and h1_headings and not _aligned(page.title, h1_headings[0].text):
        findings.append(
            _finding(
                page,
                "content.title_h1_mismatch",
                "Title and H1 are not closely aligned",
                Severity.LOW,
                "title and H1",
                "shared primary topic",
                f"title={page.title!r}; h1={h1_headings[0].text!r}",
                "Large title/H1 divergence can make the page topic less consistent across key HTML signals.",
                "Align the title and H1 around the same primary topic while keeping each useful for its context.",
                f"Compare title and H1 copy on {page.page_url}.",
                0.75,
            )
        )

    if options.flag_meta_description_misaligned and page.meta_description and not _description_aligned(page.meta_description, page.plain_text, options):
        findings.append(
            _finding(
                page,
                "content.meta_description_misaligned",
                "Meta description is not aligned with main content",
                Severity.LOW,
                "meta description and main content",
                "description terms reflected in content",
                page.meta_description,
                "A description that is disconnected from the visible content can set inaccurate expectations.",
                "Rewrite the meta description so it summarizes the actual page content.",
                f"Compare meta description against body copy on {page.page_url}.",
                0.7,
            )
        )

    if _link_density(page) > options.high_link_density_threshold:
        findings.append(
            _finding(
                page,
                "content.high_link_density",
                "Main content has high link density",
                Severity.LOW,
                "main content links",
                f"<= {options.high_link_density_threshold:.2f}",
                f"{_link_density(page):.2f}",
                "Very link-heavy main content can look more like navigation or a directory than helpful page body copy.",
                "Reduce unnecessary links or add explanatory body copy around important links.",
                f"Review link density in main content on {page.page_url}.",
                0.85,
            )
        )

    if page.images_missing_alt_count > 0:
        findings.append(
            _finding(
                page,
                "content.image_alt_gap",
                "Images inside main content have missing or empty alt text",
                Severity.LOW,
                "main content images",
                "alt text for meaningful images",
                page.images_missing_alt_count,
                "Images without useful alt text can reduce accessibility and remove context from content extraction.",
                "Add concise alt text for meaningful images, or explicit empty alt only for decorative images.",
                f"Review main content image alt text on {page.page_url}.",
                0.9,
            )
        )

    if 0 < page.paragraph_count < options.low_paragraph_threshold:
        findings.append(
            _finding(
                page,
                "content.low_paragraph_count",
                "Main content has a low paragraph count",
                Severity.LOW,
                "paragraph count",
                f">= {options.low_paragraph_threshold}",
                page.paragraph_count,
                "Very few paragraphs can indicate content that is too sparse for informational intent.",
                "Add structured explanatory copy when the page purpose requires more context.",
                f"Review paragraph depth on {page.page_url}.",
                0.8,
            )
        )

    if page.confidence < options.low_confidence_threshold:
        findings.append(
            _finding(
                page,
                "content.low_extraction_confidence",
                "Main content extraction confidence is low",
                Severity.MEDIUM,
                "content extraction",
                f">= {options.low_confidence_threshold:.2f}",
                f"{page.confidence:.2f}",
                "Low confidence means the extracted body may include boilerplate or miss important page content.",
                "Improve semantic HTML landmarks such as main/article or adjust templates to expose clear main content.",
                f"Inspect extracted selector and content for {page.page_url}.",
                0.9,
            )
        )

    if options.flag_boilerplate_heavy_extraction and _is_boilerplate_heavy(page):
        findings.append(
            _finding(
                page,
                "content.boilerplate_heavy_extraction",
                "Extraction shows boilerplate-heavy signals",
                Severity.LOW,
                "content extraction",
                "body copy with lower link pressure",
                f"links={page.link_count}; words={page.word_count}",
                "Boilerplate-heavy extraction can dilute page-specific quality signals with navigation or repeated template text.",
                "Review whether the selected main container excludes navigation, footer and repeated template elements.",
                f"Inspect extracted main selector for {page.page_url}.",
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
) -> ContentQualityFinding:
    return ContentQualityFinding(
        id=finding_id,
        title=title,
        severity=severity,
        category=IssueCategory.CONTENT,
        page_url=page.page_url,
        evidence=[Evidence(source=source, selector=page.main_selector, expected=expected, observed=observed)],
        risk=risk,
        recommendation=recommendation,
        next_action=next_action,
        confidence=confidence,
    )


def _build_summary(
    pages: list[ExtractedMainContent],
    findings: list[ContentQualityFinding],
    options: ContentQualityAuditOptions,
) -> ContentQualitySummary:
    by_severity = Counter(str(finding.severity) for finding in findings)
    by_category = Counter(str(finding.category) for finding in findings)
    finding_pages = _finding_pages(findings)
    return ContentQualitySummary(
        total_pages=len(pages),
        findings_total=len(findings),
        by_severity=dict(sorted(by_severity.items())),
        by_category=dict(sorted(by_category.items())),
        thin_content_pages=len(finding_pages.get("content.thin_content", set())),
        missing_h1_pages=len(finding_pages.get("content.missing_h1", set())),
        multiple_h1_pages=len(finding_pages.get("content.multiple_h1", set())),
        missing_title_pages=len(finding_pages.get("content.missing_title", set())),
        missing_meta_description_pages=len(finding_pages.get("content.missing_meta_description", set())),
        high_link_density_pages=len(finding_pages.get("content.high_link_density", set())),
        low_confidence_pages=sum(1 for page in pages if page.confidence < options.low_confidence_threshold),
    )


def _finding_pages(findings: list[ContentQualityFinding]) -> dict[str, set[str]]:
    pages_by_finding: dict[str, set[str]] = {}
    for finding in findings:
        pages_by_finding.setdefault(finding.id, set()).add(finding.page_url)
    return pages_by_finding


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _link_density(page: ExtractedMainContent) -> float:
    return page.link_count / page.word_count if page.word_count else 0.0


def _has_weak_heading_structure(page: ExtractedMainContent) -> bool:
    if not page.headings:
        return False
    levels = [heading.level for heading in page.headings]
    if levels[0] != 1:
        return True
    return any(current - previous > 1 for previous, current in zip(levels, levels[1:]))


def _heading_sequence(page: ExtractedMainContent) -> str:
    return " > ".join(f"h{heading.level}" for heading in page.headings) or "none"


def _aligned(left: str, right: str) -> bool:
    left_norm = _normalized_text(left)
    right_norm = _normalized_text(right)
    if not left_norm or not right_norm:
        return False
    return left_norm in right_norm or right_norm in left_norm or bool(_tokens(left_norm) & _tokens(right_norm))


def _description_aligned(description: str, plain_text: str, options: ContentQualityAuditOptions) -> bool:
    description_tokens = _tokens(description)
    if not description_tokens:
        return True
    body_tokens = _tokens(plain_text)
    overlap = len(description_tokens & body_tokens) / len(description_tokens)
    return overlap >= options.min_meta_alignment_overlap


def _tokens(text: str) -> set[str]:
    return {word for word in _WORD_RE.findall(_normalized_text(text)) if len(word) > 2 and word not in _STOPWORDS}


def _normalized_text(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


def _is_boilerplate_heavy(page: ExtractedMainContent) -> bool:
    return page.boilerplate_removed and page.link_count >= 10 and _link_density(page) > 0.1
