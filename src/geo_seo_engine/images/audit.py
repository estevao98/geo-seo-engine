from __future__ import annotations

from collections import Counter

from geo_seo_engine.core.models import Evidence, IssueCategory, Severity
from geo_seo_engine.images.models import (
    ImageAuditFinding,
    ImageAuditOptions,
    ImageAuditResult,
    ImageAuditSummary,
    ImageResource,
    PageImageInventory,
    SkippedImage,
)


def run_image_audit(
    pages: list[PageImageInventory],
    options: ImageAuditOptions | None = None,
    start_url: str | None = None,
) -> ImageAuditResult:
    audit_options = options or ImageAuditOptions()
    findings: list[ImageAuditFinding] = []

    for page in pages:
        for skipped in page.skipped_images:
            if skipped.reason == "missing_src":
                findings.append(_missing_src_finding(skipped))

        for image in page.images:
            if audit_options.flag_missing_alt and not image.has_alt_attribute:
                findings.append(_missing_alt_finding(image))
            if _should_flag_empty_alt(image, audit_options):
                findings.append(_empty_alt_finding(image))
            if audit_options.flag_missing_dimensions and _has_missing_dimensions(image):
                findings.append(_missing_dimensions_finding(image))
            if audit_options.flag_external_images and image.is_external:
                findings.append(_external_host_finding(image))
            if audit_options.flag_data_uri and image.is_data_uri:
                findings.append(_data_uri_finding(image))
            if audit_options.flag_missing_lazy_loading and _missing_lazy_loading(image):
                findings.append(_missing_lazy_loading_finding(image))

    return ImageAuditResult(
        start_url=start_url,
        pages=pages,
        findings=findings,
        summary=_build_summary(pages, findings),
    )


def _missing_src_finding(skipped: SkippedImage) -> ImageAuditFinding:
    return ImageAuditFinding(
        id="image.missing_src",
        title="Image tag is missing a usable src attribute",
        severity=Severity.MEDIUM,
        category=IssueCategory.TECHNICAL,
        page_url=skipped.page_url,
        image_url=None,
        evidence=[
            Evidence(
                source="html.img",
                selector="img[src]",
                value=skipped.raw_src,
                expected="non-empty src",
                observed=skipped.raw_src,
            )
        ],
        risk=(
            "An image element without a usable source can create broken visual content and "
            "adds noise to static HTML analysis."
        ),
        recommendation="Provide a valid src or remove the image element if it is not needed.",
        next_action=f"Inspect image tags without src on {skipped.page_url}.",
        confidence=1.0,
    )


def _missing_alt_finding(image: ImageResource) -> ImageAuditFinding:
    return ImageAuditFinding(
        id="image.missing_alt_attribute",
        title="Image is missing an alt attribute",
        severity=Severity.MEDIUM,
        category=IssueCategory.CONTENT,
        page_url=image.page_url,
        image_url=image.normalized_src,
        evidence=[
            Evidence(
                source="html.img",
                selector="img[alt]",
                value=image.raw_src,
                expected="alt attribute present",
                observed="missing",
            )
        ],
        risk=(
            "Missing alt text can reduce accessibility and makes the image context less clear "
            "to systems that rely on HTML text signals."
        ),
        recommendation=(
            "Add concise alt text for meaningful images, or use an explicit empty alt only "
            "when the image is decorative."
        ),
        next_action=f"Review whether {image.normalized_src} needs descriptive alt text.",
        confidence=0.95,
    )


def _empty_alt_finding(image: ImageResource) -> ImageAuditFinding:
    return ImageAuditFinding(
        id="image.empty_alt_attribute",
        title="Image has an empty alt attribute",
        severity=Severity.INFO,
        category=IssueCategory.CONTENT,
        page_url=image.page_url,
        image_url=image.normalized_src,
        evidence=[
            Evidence(
                source="html.img",
                selector="img[alt]",
                value=image.alt,
                expected="descriptive alt for meaningful images or empty alt for decorative images",
                observed="empty alt",
            )
        ],
        risk=(
            "An empty alt attribute can be correct for decorative images, but meaningful "
            "images may need text alternatives for accessibility and context."
        ),
        recommendation=(
            "Confirm the image is decorative. If it carries information, replace the empty "
            "alt with concise descriptive text."
        ),
        next_action=f"Classify {image.normalized_src} as decorative or meaningful.",
        confidence=0.8,
    )


def _missing_dimensions_finding(image: ImageResource) -> ImageAuditFinding:
    return ImageAuditFinding(
        id="image.missing_dimensions",
        title="Image tag is missing width or height attributes",
        severity=Severity.LOW,
        category=IssueCategory.PERFORMANCE,
        page_url=image.page_url,
        image_url=image.normalized_src,
        evidence=[
            Evidence(
                source="html.img",
                selector="img[width][height]",
                value=image.raw_src,
                expected="width and height attributes",
                observed=f"width={image.width!r}, height={image.height!r}",
            )
        ],
        risk=(
            "Missing intrinsic dimensions can make potential layout stability harder to reason "
            "about, although CSS or framework-level sizing may already handle this."
        ),
        recommendation="Declare width and height where the rendered image dimensions are known.",
        next_action=f"Check sizing strategy for {image.normalized_src} on {image.page_url}.",
        confidence=0.85,
    )


def _external_host_finding(image: ImageResource) -> ImageAuditFinding:
    return ImageAuditFinding(
        id="image.external_host",
        title="Image is loaded from a host outside the configured scope",
        severity=Severity.INFO,
        category=IssueCategory.TECHNICAL,
        page_url=image.page_url,
        image_url=image.normalized_src,
        evidence=[
            Evidence(
                source="html.img",
                selector="img[src]",
                value=image.normalized_src,
                expected="configured allowed hosts",
                observed=image.normalized_src,
            )
        ],
        risk=(
            "External image hosts can be intentional, such as a CDN or asset host, but they add "
            "a dependency outside the audited crawl scope."
        ),
        recommendation="Confirm the external host is intentional, reliable, and covered by your asset policy.",
        next_action=f"Validate ownership or CDN policy for {image.normalized_src}.",
        confidence=0.9,
    )


def _data_uri_finding(image: ImageResource) -> ImageAuditFinding:
    return ImageAuditFinding(
        id="image.data_uri",
        title="Image source is embedded as a data URI",
        severity=Severity.INFO,
        category=IssueCategory.PERFORMANCE,
        page_url=image.page_url,
        image_url=image.normalized_src,
        evidence=[
            Evidence(
                source="html.img",
                selector="img[src^='data:']",
                value="data URI",
                expected="external or relative image URL when appropriate",
                observed="data URI",
            )
        ],
        risk=(
            "Data URI images can be intentional for tiny assets, but they increase HTML size "
            "and cannot be audited here as separate image resources."
        ),
        recommendation="Keep data URI usage limited to intentional small decorative assets.",
        next_action=f"Review whether the data URI image on {image.page_url} should remain inline.",
        confidence=0.9,
    )


def _missing_lazy_loading_finding(image: ImageResource) -> ImageAuditFinding:
    return ImageAuditFinding(
        id="image.missing_lazy_loading",
        title="Image may be a lazy-loading candidate",
        severity=Severity.INFO,
        category=IssueCategory.PERFORMANCE,
        page_url=image.page_url,
        image_url=image.normalized_src,
        evidence=[
            Evidence(
                source="html.img",
                selector="img[loading]",
                value=image.loading,
                expected="lazy where appropriate",
                observed=image.loading or "missing",
            )
        ],
        risk=(
            "Some below-the-fold images can benefit from lazy loading, but above-the-fold or "
            "critical images may intentionally load eagerly."
        ),
        recommendation="Apply lazy loading selectively after confirming the image is not critical above-the-fold content.",
        next_action=f"Decide whether {image.normalized_src} is a safe lazy-loading candidate.",
        confidence=0.65,
    )


def _build_summary(
    pages: list[PageImageInventory],
    findings: list[ImageAuditFinding],
) -> ImageAuditSummary:
    images = [image for page in pages for image in page.images]
    skipped_images = [skipped for page in pages for skipped in page.skipped_images]
    by_severity = Counter(str(finding.severity) for finding in findings)
    by_category = Counter(str(finding.category) for finding in findings)

    return ImageAuditSummary(
        total_pages=len(pages),
        total_images=len(images),
        findings_total=len(findings),
        by_severity=dict(sorted(by_severity.items())),
        by_category=dict(sorted(by_category.items())),
        missing_src_images=sum(1 for skipped in skipped_images if skipped.reason == "missing_src"),
        missing_alt_images=sum(1 for image in images if not image.has_alt_attribute),
        empty_alt_images=sum(1 for image in images if _is_empty_alt_non_decorative(image)),
        missing_dimension_images=sum(1 for image in images if _has_missing_dimensions(image)),
        external_images=sum(1 for image in images if image.is_external),
        data_uri_images=sum(1 for image in images if image.is_data_uri),
        decorative_images=sum(1 for image in images if image.is_decorative),
    )


def _is_empty(value: str | None) -> bool:
    return value is not None and value.strip() == ""


def _should_flag_empty_alt(image: ImageResource, audit_options: ImageAuditOptions) -> bool:
    return audit_options.flag_empty_alt and _is_empty_alt_non_decorative(image)


def _is_empty_alt_non_decorative(image: ImageResource) -> bool:
    return image.has_alt_attribute and _is_empty(image.alt) and not image.is_decorative


def _has_missing_dimensions(image: ImageResource) -> bool:
    return not image.width or not image.height


def _missing_lazy_loading(image: ImageResource) -> bool:
    return (image.loading or "").strip().lower() != "lazy"
