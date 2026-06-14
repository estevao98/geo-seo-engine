import json

from geo_seo_engine.content import ContentHeading, ExtractedMainContent, extract_main_content_from_html
from geo_seo_engine.content_quality import ContentQualityAuditOptions, run_content_quality_audit


def test_generates_missing_main_content_finding():
    result = run_content_quality_audit([_page(plain_text="", word_count=0, confidence=0.0)])

    assert "content.missing_main_content" in _finding_ids(result)


def test_generates_thin_content_finding():
    result = run_content_quality_audit([_page(word_count=20, plain_text="short body copy")])

    assert "content.thin_content" in _finding_ids(result)


def test_adequate_content_does_not_generate_thin_finding():
    result = run_content_quality_audit([_adequate_page()])

    assert "content.thin_content" not in _finding_ids(result)


def test_generates_missing_h1_finding():
    result = run_content_quality_audit([_page(headings=[])])

    assert "content.missing_h1" in _finding_ids(result)


def test_generates_multiple_h1_finding():
    result = run_content_quality_audit(
        [_page(headings=[ContentHeading(level=1, text="One", order=0), ContentHeading(level=1, text="Two", order=1)])]
    )

    assert "content.multiple_h1" in _finding_ids(result)


def test_generates_weak_heading_structure_finding():
    result = run_content_quality_audit(
        [_page(headings=[ContentHeading(level=1, text="Guide", order=0), ContentHeading(level=3, text="Details", order=1)])]
    )

    assert "content.weak_heading_structure" in _finding_ids(result)


def test_generates_title_h1_mismatch_finding():
    result = run_content_quality_audit(
        [_page(title="Pricing plans", headings=[ContentHeading(level=1, text="Developer documentation", order=0)])]
    )

    assert "content.title_h1_mismatch" in _finding_ids(result)


def test_generates_missing_title_finding():
    result = run_content_quality_audit([_page(title=None)])

    assert "content.missing_title" in _finding_ids(result)


def test_generates_missing_meta_description_finding():
    result = run_content_quality_audit([_page(meta_description=None)])

    assert "content.missing_meta_description" in _finding_ids(result)


def test_generates_meta_description_misaligned_finding():
    result = run_content_quality_audit(
        [
            _page(
                meta_description="Enterprise billing automation for finance teams.",
                plain_text="Banana recipes and garden notes for weekend cooking.",
            )
        ]
    )

    assert "content.meta_description_misaligned" in _finding_ids(result)


def test_generates_high_link_density_finding():
    result = run_content_quality_audit([_page(word_count=20, link_count=8)])

    assert "content.high_link_density" in _finding_ids(result)


def test_generates_image_alt_gap_from_extracted_content():
    result = run_content_quality_audit([_page(image_count=2, images_missing_alt_count=1)])

    assert "content.image_alt_gap" in _finding_ids(result)


def test_generates_low_paragraph_count_finding():
    result = run_content_quality_audit([_page(paragraph_count=1)])

    assert "content.low_paragraph_count" in _finding_ids(result)


def test_generates_low_extraction_confidence_finding():
    result = run_content_quality_audit([_page(confidence=0.2)])

    assert "content.low_extraction_confidence" in _finding_ids(result)


def test_generates_boilerplate_heavy_extraction_finding():
    result = run_content_quality_audit([_page(word_count=80, link_count=12, boilerplate_removed=True)])

    assert "content.boilerplate_heavy_extraction" in _finding_ids(result)


def test_summary_counts_pages_and_findings():
    result = run_content_quality_audit(
        [
            _adequate_page(page_url="https://example.com/a", title=None, headings=[]),
            _page(page_url="https://example.com/b", word_count=20, link_count=8, confidence=0.2),
        ],
        start_url="https://example.com/",
    )

    assert result.start_url == "https://example.com/"
    assert result.summary.total_pages == 2
    assert result.summary.findings_total == len(result.findings)
    assert result.summary.thin_content_pages == 1
    assert result.summary.missing_h1_pages == 1
    assert result.summary.missing_title_pages == 1
    assert result.summary.high_link_density_pages == 1
    assert result.summary.low_confidence_pages == 1
    assert result.summary.by_category == {"content": len(result.findings)}


def test_output_is_json_serializable():
    result = run_content_quality_audit([_page(title=None)])

    rendered = json.dumps(result.model_dump(mode="json"), sort_keys=True)

    assert "content.missing_title" in rendered


def test_extraction_preserves_main_content_image_alt_gap_signals():
    page = extract_main_content_from_html(
        '<main><h1>Guide</h1><p>Helpful body copy.</p><img src="/a.png"><img src="/b.png" alt="Chart"></main>',
        "https://example.com/",
    )

    assert page.image_count == 2
    assert page.images_missing_alt_count == 1
    assert page.image_alt_texts == ["Chart"]


def test_audit_options_can_disable_noisy_alignment_checks():
    result = run_content_quality_audit(
        [
            _page(
                title="Pricing plans",
                meta_description="Enterprise billing automation for finance teams.",
                headings=[ContentHeading(level=1, text="Developer documentation", order=0)],
                plain_text="Banana recipes and garden notes for weekend cooking.",
            )
        ],
        options=ContentQualityAuditOptions(flag_title_h1_mismatch=False, flag_meta_description_misaligned=False),
    )

    assert "content.title_h1_mismatch" not in _finding_ids(result)
    assert "content.meta_description_misaligned" not in _finding_ids(result)


def _adequate_page(**overrides):
    text = " ".join(["useful guide content"] * 120)
    data = {"plain_text": text, "word_count": 360, "paragraph_count": 3}
    data.update(overrides)
    return _page(**data)


def _page(**overrides):
    text = overrides.pop("plain_text", "Useful guide content for users and teams.")
    word_count = overrides.pop("word_count", len(text.split()))
    data = {
        "page_url": "https://example.com/page",
        "title": "Useful guide",
        "meta_description": "Useful guide content for users.",
        "canonical_url": None,
        "extraction_method": "main_element",
        "main_selector": "main",
        "confidence": 0.95,
        "headings": [ContentHeading(level=1, text="Useful guide", order=0)],
        "text_blocks": [],
        "links": [],
        "image_alt_texts": [],
        "plain_text": text,
        "word_count": word_count,
        "character_count": len(text),
        "paragraph_count": 2,
        "heading_count": 1,
        "link_count": 0,
        "internal_link_count": 0,
        "external_link_count": 0,
        "image_count": 0,
        "images_missing_alt_count": 0,
        "boilerplate_removed": False,
    }
    data.update(overrides)
    return ExtractedMainContent(**data)


def _finding_ids(result):
    return [finding.id for finding in result.findings]
