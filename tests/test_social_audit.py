import json

from geo_seo_engine.social import extract_social_metadata_from_html, run_social_metadata_audit


def test_generates_missing_og_title_finding():
    page = extract_social_metadata_from_html("", "https://example.com/page")

    result = run_social_metadata_audit([page])

    finding = _finding_by_id(result, "social.missing_og_title")
    assert finding.severity == "medium"


def test_generates_missing_og_description_finding():
    page = extract_social_metadata_from_html('<meta property="og:title" content="Title">', "https://example.com/page")

    result = run_social_metadata_audit([page])

    finding = _finding_by_id(result, "social.missing_og_description")
    assert finding.severity == "medium"


def test_generates_missing_og_image_finding():
    page = extract_social_metadata_from_html('<meta property="og:title" content="Title">', "https://example.com/page")

    result = run_social_metadata_audit([page])

    finding = _finding_by_id(result, "social.missing_og_image")
    assert finding.severity == "medium"


def test_generates_missing_og_url_finding():
    page = extract_social_metadata_from_html('<meta property="og:title" content="Title">', "https://example.com/page")

    result = run_social_metadata_audit([page])

    finding = _finding_by_id(result, "social.missing_og_url")
    assert finding.severity == "low"


def test_generates_missing_twitter_card_finding():
    page = extract_social_metadata_from_html("", "https://example.com/page")

    result = run_social_metadata_audit([page])

    finding = _finding_by_id(result, "social.missing_twitter_card")
    assert finding.severity == "low"


def test_missing_twitter_fields_have_reduced_severity_when_og_fallback_exists():
    page = extract_social_metadata_from_html(
        """
        <meta property="og:title" content="Title">
        <meta property="og:description" content="Description">
        <meta property="og:image" content="https://example.com/social.png">
        <meta property="og:url" content="https://example.com/page">
        <meta name="twitter:card" content="summary_large_image">
        """,
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])

    assert _finding_by_id(result, "social.missing_twitter_title").severity == "info"
    assert _finding_by_id(result, "social.missing_twitter_description").severity == "info"
    assert _finding_by_id(result, "social.missing_twitter_image").severity == "info"


def test_generates_empty_content_finding():
    page = extract_social_metadata_from_html('<meta property="og:title" content="">', "https://example.com/page")

    result = run_social_metadata_audit([page])
    finding = _finding_by_id(result, "social.empty_meta_content")

    assert finding.metadata_key == "og:title"
    assert finding.severity == "medium"


def test_generates_duplicate_tag_finding():
    page = extract_social_metadata_from_html(
        '<meta property="og:title" content="A"><meta property="og:title" content="B">',
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])
    finding = _finding_by_id(result, "social.duplicate_meta_tag")

    assert finding.metadata_key == "og:title"
    assert finding.severity == "low"


def test_generates_relative_social_image_url_finding():
    page = extract_social_metadata_from_html(
        '<meta property="og:image" content="/social.png">',
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])
    finding = _finding_by_id(result, "social.relative_image_url")

    assert finding.severity == "low"
    assert "compatibility" in finding.risk


def test_generates_invalid_social_image_url_finding():
    page = extract_social_metadata_from_html(
        '<meta property="og:image" content="data:image/png;base64,AAAA">',
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])
    finding = _finding_by_id(result, "social.invalid_image_url")

    assert finding.severity == "medium"


def test_generates_external_social_image_host_as_info():
    page = extract_social_metadata_from_html(
        '<meta property="og:image" content="https://cdn.example.net/social.png">',
        "https://example.com/page",
        allowed_hosts=["example.com"],
    )

    result = run_social_metadata_audit([page])
    finding = _finding_by_id(result, "social.external_image_host")

    assert finding.severity == "info"
    assert "CDN" in finding.risk


def test_summary_counts_pages_findings_categories_and_severities():
    page = extract_social_metadata_from_html(
        """
        <meta property="og:title" content="">
        <meta property="og:title" content="Title">
        <meta property="og:image" content="/social.png">
        <meta property="og:image" content="https://cdn.example.net/social.png">
        <meta name="twitter:image" content="data:image/png;base64,AAAA">
        """,
        "https://example.com/page",
        allowed_hosts=["example.com"],
    )

    result = run_social_metadata_audit([page], start_url="https://example.com/")

    assert result.start_url == "https://example.com/"
    assert result.summary.total_pages == 1
    assert result.summary.findings_total == len(result.findings)
    assert result.summary.by_severity["medium"] >= 1
    assert result.summary.by_category["content"] >= 1
    assert result.summary.pages_missing_og_description == 1
    assert result.summary.pages_missing_og_url == 1
    assert result.summary.pages_missing_twitter_card == 1
    assert result.summary.duplicate_tag_pages == 1
    assert result.summary.empty_content_tags == 1
    assert result.summary.external_social_images == 1
    assert result.summary.relative_social_images == 1
    assert result.summary.invalid_social_images == 1


def test_output_is_json_serializable():
    page = extract_social_metadata_from_html('<meta property="og:title" content="Title">', "https://example.com/page")
    result = run_social_metadata_audit([page])

    rendered = json.dumps(result.model_dump(mode="json"))

    assert "social.missing_og_description" in rendered


def _finding_by_id(result, finding_id):
    return next(finding for finding in result.findings if finding.id == finding_id)
