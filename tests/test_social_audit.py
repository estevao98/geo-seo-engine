import json

from geo_seo_engine.social import SocialAuditOptions, extract_social_metadata_from_html, run_social_metadata_audit


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


def test_missing_twitter_fields_use_open_graph_fallback_without_findings():
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

    assert "social.missing_twitter_title" not in _finding_ids(result)
    assert "social.missing_twitter_description" not in _finding_ids(result)
    assert "social.missing_twitter_image" not in _finding_ids(result)
    assert result.pages[0].used_open_graph_fallback_fields == [
        "twitter:title",
        "twitter:description",
        "twitter:image",
    ]


def test_generates_empty_content_finding():
    page = extract_social_metadata_from_html('<meta property="og:title" content="">', "https://example.com/page")

    result = run_social_metadata_audit([page])
    finding = _finding_by_id(result, "social.empty_meta_content")

    assert finding.metadata_key == "og:title"
    assert finding.severity == "medium"
    assert "social.missing_og_title" not in _finding_ids(result)
    assert result.summary.pages_missing_og_title == 0


def test_generates_duplicate_tag_finding_for_conflicting_singleton_values():
    page = extract_social_metadata_from_html(
        '<meta property="og:title" content="A"><meta property="og:title" content="B">',
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])
    finding = _finding_by_id(result, "social.duplicate_meta_tag")

    assert finding.metadata_key == "og:title"
    assert finding.severity == "low"


def test_multiple_different_og_images_do_not_generate_duplicate_finding():
    page = extract_social_metadata_from_html(
        """
        <meta property="og:image" content="https://example.com/a.png">
        <meta property="og:image" content="https://example.com/b.png">
        """,
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])

    assert page.duplicates == {"og:image": 2}
    assert len(page.image_references) == 2
    assert "social.duplicate_meta_tag" not in _finding_ids(result)


def test_identical_duplicate_singleton_values_do_not_generate_duplicate_finding():
    page = extract_social_metadata_from_html(
        '<meta property="og:title" content="A"><meta property="og:title" content="A">',
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])

    assert page.duplicates == {"og:title": 2}
    assert "social.duplicate_meta_tag" not in _finding_ids(result)


def test_conflicting_duplicate_twitter_card_generates_duplicate_finding():
    page = extract_social_metadata_from_html(
        '<meta name="twitter:card" content="summary"><meta name="twitter:card" content="summary_large_image">',
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])
    finding = _finding_by_id(result, "social.duplicate_meta_tag")

    assert finding.metadata_key == "twitter:card"


def test_twitter_card_missing_does_not_use_open_graph_fallback():
    page = extract_social_metadata_from_html(
        """
        <meta property="og:title" content="Title">
        <meta property="og:description" content="Description">
        <meta property="og:image" content="https://example.com/social.png">
        """,
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])

    assert _finding_by_id(result, "social.missing_twitter_card").severity == "low"
    assert "social.missing_twitter_title" not in _finding_ids(result)
    assert "social.missing_twitter_description" not in _finding_ids(result)
    assert "social.missing_twitter_image" not in _finding_ids(result)


def test_twitter_open_graph_fallback_can_be_disabled():
    page = extract_social_metadata_from_html(
        """
        <meta property="og:title" content="Title">
        <meta property="og:description" content="Description">
        <meta property="og:image" content="https://example.com/social.png">
        <meta name="twitter:card" content="summary_large_image">
        """,
        "https://example.com/page",
    )

    result = run_social_metadata_audit(
        [page],
        options=SocialAuditOptions(allow_twitter_og_fallback=False),
    )

    assert _finding_by_id(result, "social.missing_twitter_title").severity == "low"
    assert _finding_by_id(result, "social.missing_twitter_description").severity == "low"
    assert _finding_by_id(result, "social.missing_twitter_image").severity == "low"
    assert result.pages[0].used_open_graph_fallback_fields == []


def test_empty_twitter_title_uses_open_graph_fallback_without_missing_finding():
    page = extract_social_metadata_from_html(
        """
        <meta property="og:title" content="Title">
        <meta name="twitter:title" content="   ">
        """,
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])

    assert _finding_by_id(result, "social.empty_meta_content").metadata_key == "twitter:title"
    assert "social.missing_twitter_title" not in _finding_ids(result)
    assert result.pages[0].used_open_graph_fallback_fields == ["twitter:title"]


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


def test_generates_invalid_social_image_url_finding_for_javascript_scheme():
    page = extract_social_metadata_from_html(
        '<meta property="og:image" content="javascript:alert(1)">',
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])

    assert _finding_by_id(result, "social.invalid_image_url").metadata_key == "og:image"


def test_generates_invalid_social_image_url_finding_for_ftp_scheme():
    page = extract_social_metadata_from_html(
        '<meta property="og:image" content="ftp://example.com/a.jpg">',
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])

    assert _finding_by_id(result, "social.invalid_image_url").metadata_key == "og:image"


def test_generates_invalid_social_image_url_finding_for_whitespace():
    page = extract_social_metadata_from_html(
        '<meta property="og:image" content="https://example.com/social image.png">',
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])

    assert _finding_by_id(result, "social.invalid_image_url").metadata_key == "og:image"


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


def test_allowed_cdn_host_does_not_generate_external_social_image_finding():
    page = extract_social_metadata_from_html(
        '<meta property="og:image" content="https://cdn.example.com/social.png">',
        "https://example.com/page",
        allowed_hosts=["example.com", "cdn.example.com"],
    )

    result = run_social_metadata_audit([page])

    assert page.image_references[0].is_external is False
    assert "social.external_image_host" not in _finding_ids(result)


def test_relative_social_image_finding_preserves_resolved_url():
    page = extract_social_metadata_from_html(
        '<meta property="og:image" content="/social.png">',
        "https://example.com/path/page",
    )

    result = run_social_metadata_audit([page])
    finding = _finding_by_id(result, "social.relative_image_url")
    image = page.image_references[0]

    assert finding.severity == "low"
    assert image.resolved_url == "https://example.com/social.png"
    assert image.normalized_url == "https://example.com/social.png"


def test_structured_og_image_fields_do_not_generate_duplicate_finding():
    page = extract_social_metadata_from_html(
        """
        <meta property="og:image" content="https://example.com/a.png">
        <meta property="og:image:width" content="1200">
        <meta property="og:image:width" content="800">
        <meta property="og:image:height" content="630">
        <meta property="og:image:height" content="420">
        <meta property="og:image:alt" content="A">
        <meta property="og:image:alt" content="B">
        """,
        "https://example.com/page",
    )

    result = run_social_metadata_audit([page])

    assert page.duplicates == {"og:image:alt": 2, "og:image:height": 2, "og:image:width": 2}
    assert "social.duplicate_meta_tag" not in _finding_ids(result)


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


def _finding_ids(result):
    return {finding.id for finding in result.findings}
