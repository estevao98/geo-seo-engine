import json

from geo_seo_engine.images import extract_images_from_html, run_image_audit


def test_generates_missing_src_finding():
    page = extract_images_from_html("<img>", "https://example.com/")

    result = run_image_audit([page])

    assert "image.missing_src" in _finding_ids(result)


def test_generates_missing_alt_attribute_finding():
    page = extract_images_from_html('<img src="/image.png">', "https://example.com/")

    result = run_image_audit([page])

    assert "image.missing_alt_attribute" in _finding_ids(result)


def test_generates_empty_alt_attribute_finding():
    page = extract_images_from_html('<img src="/image.png" alt="">', "https://example.com/")

    result = run_image_audit([page])

    assert "image.empty_alt_attribute" in _finding_ids(result)


def test_empty_alt_with_presentation_role_does_not_generate_empty_alt_finding():
    page = extract_images_from_html('<img src="/icon.svg" alt="" role="presentation">', "https://example.com/")

    result = run_image_audit([page])

    assert "image.empty_alt_attribute" not in _finding_ids(result)


def test_empty_alt_with_aria_hidden_does_not_generate_empty_alt_finding():
    page = extract_images_from_html('<img src="/icon.svg" alt="" aria-hidden="true">', "https://example.com/")

    result = run_image_audit([page])

    assert "image.empty_alt_attribute" not in _finding_ids(result)


def test_generates_missing_dimensions_finding():
    page = extract_images_from_html('<img src="/image.png" alt="Image">', "https://example.com/")

    result = run_image_audit([page])

    finding = _finding_by_id(result, "image.missing_dimensions")
    assert finding.severity == "low"
    assert "potential layout stability" in finding.risk


def test_generates_external_host_finding_as_info():
    page = extract_images_from_html(
        '<img src="https://cdn.example.net/image.png" alt="CDN" width="10" height="10">',
        "https://example.com/",
        allowed_hosts=["example.com"],
    )

    result = run_image_audit([page])
    finding = _finding_by_id(result, "image.external_host")

    assert finding.severity == "info"
    assert "CDN or asset host" in finding.risk


def test_generates_data_uri_finding_as_info():
    page = extract_images_from_html(
        '<img src="data:image/png;base64,AAAA" alt="Inline" width="10" height="10">',
        "https://example.com/",
    )

    result = run_image_audit([page])
    finding = _finding_by_id(result, "image.data_uri")

    assert finding.severity == "info"


def test_summary_counts_pages_images_and_findings():
    page = extract_images_from_html(
        """
        <img src="/missing-alt.png">
        <img src="/empty-alt.png" alt="">
        <img>
        """,
        "https://example.com/",
    )

    result = run_image_audit([page], start_url="https://example.com/")

    assert result.start_url == "https://example.com/"
    assert result.summary.total_pages == 1
    assert result.summary.total_images == 2
    assert result.summary.findings_total == len(result.findings)
    assert result.summary.missing_src_images == 1
    assert result.summary.missing_alt_images == 1
    assert result.summary.empty_alt_images == 1
    assert result.summary.missing_dimension_images == 2


def test_output_is_json_serializable():
    page = extract_images_from_html('<img src="/image.png" alt="Image">', "https://example.com/")
    result = run_image_audit([page])

    rendered = json.dumps(result.model_dump(mode="json"))

    assert "image.missing_dimensions" in rendered


def _finding_ids(result):
    return [finding.id for finding in result.findings]


def _finding_by_id(result, finding_id):
    return next(finding for finding in result.findings if finding.id == finding_id)
