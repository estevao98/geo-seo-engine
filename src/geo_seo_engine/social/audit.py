from __future__ import annotations

from collections import Counter

from geo_seo_engine.core.models import Evidence, IssueCategory, Severity
from geo_seo_engine.social.models import (
    PageSocialMetadata,
    SocialAuditFinding,
    SocialAuditOptions,
    SocialAuditResult,
    SocialAuditSummary,
    SocialImageReference,
    SocialMetaTag,
)

OPEN_GRAPH_REQUIRED = {
    "og:title": Severity.MEDIUM,
    "og:description": Severity.MEDIUM,
    "og:image": Severity.MEDIUM,
    "og:url": Severity.LOW,
}
OPEN_GRAPH_SINGLETON_KEYS = {
    "og:title",
    "og:description",
    "og:type",
    "og:url",
    "og:site_name",
    "og:locale",
}
TWITTER_SINGLETON_KEYS = {
    "twitter:card",
    "twitter:title",
    "twitter:description",
    "twitter:image",
    "twitter:site",
    "twitter:creator",
}
SINGLETON_METADATA_KEYS = OPEN_GRAPH_SINGLETON_KEYS | TWITTER_SINGLETON_KEYS
TWITTER_REQUIRED = ("twitter:card", "twitter:title", "twitter:description", "twitter:image")
TWITTER_FALLBACKS = {
    "twitter:title": "og:title",
    "twitter:description": "og:description",
    "twitter:image": "og:image",
}


def run_social_metadata_audit(
    pages: list[PageSocialMetadata],
    options: SocialAuditOptions | None = None,
    start_url: str | None = None,
) -> SocialAuditResult:
    audit_options = options or SocialAuditOptions()
    findings: list[SocialAuditFinding] = []

    for page in pages:
        page.used_open_graph_fallback_fields = []

        if audit_options.flag_open_graph:
            for metadata_key, severity in OPEN_GRAPH_REQUIRED.items():
                if not _has_tag(page, metadata_key):
                    findings.append(_missing_open_graph_finding(page, metadata_key, severity))

        if audit_options.flag_twitter:
            for metadata_key in TWITTER_REQUIRED:
                if _has_value(page, metadata_key):
                    continue
                if _uses_open_graph_fallback(page, metadata_key, audit_options):
                    page.used_open_graph_fallback_fields.append(metadata_key)
                    continue
                if not _has_tag(page, metadata_key):
                    findings.append(_missing_twitter_finding(page, metadata_key))

        if audit_options.flag_empty_content:
            for tag in page.tags:
                if tag.is_empty:
                    findings.append(_empty_content_finding(tag))

        if audit_options.flag_duplicates:
            for metadata_key, tags in _conflicting_singleton_duplicates(page).items():
                findings.append(_duplicate_tag_finding(page, metadata_key, tags))

        for image in page.image_references:
            if image.is_invalid:
                findings.append(_invalid_image_url_finding(image))
                continue
            if audit_options.flag_relative_image_url and image.is_relative:
                findings.append(_relative_image_url_finding(image))
            if audit_options.flag_external_image_host and image.is_external:
                findings.append(_external_image_host_finding(image))

    return SocialAuditResult(
        start_url=start_url,
        pages=pages,
        findings=findings,
        summary=_build_summary(pages, findings),
    )


def _missing_open_graph_finding(
    page: PageSocialMetadata,
    metadata_key: str,
    severity: Severity,
) -> SocialAuditFinding:
    field_name = metadata_key.removeprefix("og:")
    return SocialAuditFinding(
        id=f"social.missing_og_{field_name}",
        title=f"Page is missing {metadata_key}",
        severity=severity,
        category=IssueCategory.CONTENT,
        page_url=page.page_url,
        metadata_key=metadata_key,
        evidence=[
            Evidence(
                source="html.meta",
                selector=f"meta[property='{metadata_key}']",
                expected="non-empty content attribute",
                observed="missing",
            )
        ],
        risk="Social previews may have less explicit title, description, image, or URL context.",
        recommendation=f"Add a non-empty {metadata_key} meta tag that accurately represents the page.",
        next_action=f"Review Open Graph metadata for {page.page_url}.",
        confidence=0.95,
    )


def _missing_twitter_finding(page: PageSocialMetadata, metadata_key: str) -> SocialAuditFinding:
    field_name = metadata_key.removeprefix("twitter:")
    return SocialAuditFinding(
        id=f"social.missing_twitter_{field_name}",
        title=f"Page is missing {metadata_key}",
        severity=Severity.LOW,
        category=IssueCategory.CONTENT,
        page_url=page.page_url,
        metadata_key=metadata_key,
        evidence=[
            Evidence(
                source="html.meta",
                selector=f"meta[name='{metadata_key}']",
                expected="non-empty content attribute",
                observed="missing",
            )
        ],
        risk=(
            "Twitter/X previews may have less explicit title, description, image, or card context."
        ),
        recommendation=f"Add {metadata_key} when a Twitter/X-specific preview is needed.",
        next_action=f"Compare Twitter/X preview metadata with Open Graph metadata on {page.page_url}.",
        confidence=0.9,
    )


def _empty_content_finding(tag: SocialMetaTag) -> SocialAuditFinding:
    return SocialAuditFinding(
        id="social.empty_meta_content",
        title="Social meta tag has empty content",
        severity=Severity.MEDIUM if tag.key in {"og:title", "og:description", "og:image"} else Severity.LOW,
        category=IssueCategory.CONTENT,
        page_url=tag.page_url,
        metadata_key=tag.key,
        evidence=[
            Evidence(
                source="html.meta",
                selector=f"meta[{tag.attribute_name}='{tag.raw_key}']",
                value=tag.content,
                expected="non-empty content attribute",
                observed="empty",
            )
        ],
        risk="An empty social meta tag is present but cannot provide useful preview metadata.",
        recommendation="Populate the content attribute or remove the tag if it is not needed.",
        next_action=f"Inspect the empty {tag.key} tag on {tag.page_url}.",
        confidence=1.0,
    )


def _duplicate_tag_finding(
    page: PageSocialMetadata,
    metadata_key: str,
    tags: list[SocialMetaTag],
) -> SocialAuditFinding:
    distinct_values = sorted({tag.content for tag in tags})
    return SocialAuditFinding(
        id="social.duplicate_meta_tag",
        title="Social meta tag has conflicting duplicates",
        severity=Severity.LOW,
        category=IssueCategory.TECHNICAL,
        page_url=page.page_url,
        metadata_key=metadata_key,
        evidence=[
            Evidence(
                source="html.meta",
                selector=f"meta[property='{metadata_key}'], meta[name='{metadata_key}']",
                value=" | ".join(distinct_values),
                expected="one value for singleton social metadata keys",
                observed=f"{len(tags)} tags with {len(distinct_values)} distinct values",
            )
        ],
        risk="Duplicate social meta tags can make preview behavior ambiguous across parsers.",
        recommendation="Keep one canonical value for each singleton social metadata key.",
        next_action=f"Consolidate duplicate {metadata_key} tags on {page.page_url}.",
        confidence=0.9,
    )


def _invalid_image_url_finding(image: SocialImageReference) -> SocialAuditFinding:
    return SocialAuditFinding(
        id="social.invalid_image_url",
        title="Social image URL is invalid or unsupported",
        severity=Severity.MEDIUM,
        category=IssueCategory.TECHNICAL,
        page_url=image.page_url,
        metadata_key=image.metadata_key,
        evidence=[
            Evidence(
                source="html.meta",
                selector=f"meta[content][property='{image.metadata_key}'], meta[content][name='{image.metadata_key}']",
                value="data URI" if image.is_data_uri else image.raw_url,
                expected="absolute HTTP(S) image URL",
                observed="invalid or unsupported URL",
            )
        ],
        risk="Invalid or unsupported social image URLs may not be usable by preview parsers.",
        recommendation="Use a valid HTTP(S) image URL for social preview image metadata.",
        next_action=f"Replace the {image.metadata_key} image URL on {image.page_url}.",
        confidence=0.95,
    )


def _relative_image_url_finding(image: SocialImageReference) -> SocialAuditFinding:
    return SocialAuditFinding(
        id="social.relative_image_url",
        title="Social image URL is relative",
        severity=Severity.LOW,
        category=IssueCategory.TECHNICAL,
        page_url=image.page_url,
        metadata_key=image.metadata_key,
        evidence=[
            Evidence(
                source="html.meta",
                selector=f"meta[content][property='{image.metadata_key}'], meta[content][name='{image.metadata_key}']",
                value=image.raw_url,
                expected="absolute HTTP(S) image URL",
                observed=image.resolved_url,
            )
        ],
        risk="Relative social image URLs can reduce compatibility with some preview parsers.",
        recommendation="Prefer an absolute HTTP(S) URL for Open Graph and Twitter/X image tags.",
        next_action=f"Convert {image.metadata_key} to an absolute image URL on {image.page_url}.",
        confidence=0.9,
    )


def _external_image_host_finding(image: SocialImageReference) -> SocialAuditFinding:
    return SocialAuditFinding(
        id="social.external_image_host",
        title="Social image is hosted outside the configured scope",
        severity=Severity.INFO,
        category=IssueCategory.TECHNICAL,
        page_url=image.page_url,
        metadata_key=image.metadata_key,
        evidence=[
            Evidence(
                source="html.meta",
                selector=f"meta[content][property='{image.metadata_key}'], meta[content][name='{image.metadata_key}']",
                value=image.normalized_url,
                expected="configured allowed hosts or intentional CDN host",
                observed=image.normalized_url,
            )
        ],
        risk="External social image hosts can be intentional CDN usage, but they add a dependency outside the crawl scope.",
        recommendation="Confirm the external social image host is intentional and covered by your asset policy.",
        next_action=f"Validate the host used by {image.metadata_key} on {image.page_url}.",
        confidence=0.85,
    )


def _build_summary(
    pages: list[PageSocialMetadata],
    findings: list[SocialAuditFinding],
) -> SocialAuditSummary:
    by_severity = Counter(str(finding.severity) for finding in findings)
    by_category = Counter(str(finding.category) for finding in findings)
    images = [image for page in pages for image in page.image_references]

    return SocialAuditSummary(
        total_pages=len(pages),
        findings_total=len(findings),
        by_severity=dict(sorted(by_severity.items())),
        by_category=dict(sorted(by_category.items())),
        pages_missing_og_title=sum(1 for page in pages if not _has_tag(page, "og:title")),
        pages_missing_og_description=sum(1 for page in pages if not _has_tag(page, "og:description")),
        pages_missing_og_image=sum(1 for page in pages if not _has_tag(page, "og:image")),
        pages_missing_og_url=sum(1 for page in pages if not _has_tag(page, "og:url")),
        pages_missing_twitter_card=sum(1 for page in pages if not _has_tag(page, "twitter:card")),
        duplicate_tag_pages=sum(1 for page in pages if _conflicting_singleton_duplicates(page)),
        empty_content_tags=sum(1 for page in pages for tag in page.tags if tag.is_empty),
        external_social_images=sum(1 for image in images if image.is_external and not image.is_invalid),
        relative_social_images=sum(1 for image in images if image.is_relative and not image.is_invalid),
        invalid_social_images=sum(1 for image in images if image.is_invalid),
    )


def _has_value(page: PageSocialMetadata, metadata_key: str) -> bool:
    values = page.open_graph if metadata_key.startswith("og:") else page.twitter
    return bool((values.get(metadata_key) or "").strip())


def _has_tag(page: PageSocialMetadata, metadata_key: str) -> bool:
    return any(tag.key == metadata_key for tag in page.tags)


def _uses_open_graph_fallback(
    page: PageSocialMetadata,
    metadata_key: str,
    audit_options: SocialAuditOptions,
) -> bool:
    if not audit_options.allow_twitter_og_fallback:
        return False
    fallback_key = TWITTER_FALLBACKS.get(metadata_key)
    return bool(fallback_key and _has_value(page, fallback_key))


def _conflicting_singleton_duplicates(page: PageSocialMetadata) -> dict[str, list[SocialMetaTag]]:
    duplicates: dict[str, list[SocialMetaTag]] = {}
    for metadata_key in sorted(page.duplicates):
        if metadata_key not in SINGLETON_METADATA_KEYS:
            continue
        tags = [tag for tag in page.tags if tag.key == metadata_key]
        if len({tag.content for tag in tags}) > 1:
            duplicates[metadata_key] = tags
    return duplicates
