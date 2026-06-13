import json

from geo_seo_engine.i18n import HreflangAuditOptions, extract_hreflang_from_html, run_hreflang_audit


def test_generates_missing_href_and_missing_hreflang_findings():
    page = extract_hreflang_from_html(
        """
        <head>
          <link rel="alternate" hreflang="en">
          <link rel="alternate" href="https://example.com/pt-br/">
        </head>
        """,
        "https://example.com/en/",
    )

    result = run_hreflang_audit([page])

    assert "hreflang.missing_href" in _finding_ids(result)
    assert "hreflang.missing_hreflang" in _finding_ids(result)


def test_generates_invalid_hreflang_and_invalid_url_findings():
    page = extract_hreflang_from_html(
        """
        <head>
          <link rel="alternate" hreflang="US" href="https://example.com/us/">
          <link rel="alternate" hreflang="pt_BR" href="https://example.com/pt-br/">
          <link rel="alternate" hreflang="es" href="ftp://example.com/es/">
        </head>
        """,
        "https://example.com/en/",
    )

    result = run_hreflang_audit([page])

    assert _finding_ids(result).count("hreflang.invalid_hreflang") == 2
    assert "hreflang.invalid_url" in _finding_ids(result)


def test_generates_relative_duplicate_external_and_missing_self_findings():
    page = extract_hreflang_from_html(
        """
        <head>
          <link rel="alternate" hreflang="pt-BR" href="/pt-br/">
          <link rel="alternate" hreflang="pt-br" href="https://example.com/br/">
          <link rel="alternate" hreflang="fr" href="https://example.fr/fr/">
        </head>
        """,
        "https://example.com/en/",
        allowed_hosts=["example.com"],
    )

    result = run_hreflang_audit([page])
    ids = _finding_ids(result)

    assert "hreflang.relative_url" in ids
    assert "hreflang.duplicate_value" in ids
    assert "hreflang.external_host" in ids
    assert "hreflang.missing_self_reference" in ids


def test_does_not_flag_missing_self_reference_when_present():
    page = extract_hreflang_from_html(
        """
        <head>
          <link rel="alternate" hreflang="en" href="https://example.com/en/">
          <link rel="alternate" hreflang="pt-BR" href="https://example.com/pt-br/">
        </head>
        """,
        "https://example.com/en/",
    )

    result = run_hreflang_audit([page])

    assert "hreflang.missing_self_reference" not in _finding_ids(result)


def test_reciprocal_link_present_does_not_generate_finding():
    en = extract_hreflang_from_html(
        """
        <head>
          <link rel="alternate" hreflang="en" href="https://example.com/en/">
          <link rel="alternate" hreflang="pt-BR" href="https://example.com/pt-br/">
        </head>
        """,
        "https://example.com/en/",
    )
    pt = extract_hreflang_from_html(
        """
        <head>
          <link rel="alternate" hreflang="pt-BR" href="https://example.com/pt-br/">
          <link rel="alternate" hreflang="en" href="https://example.com/en/">
        </head>
        """,
        "https://example.com/pt-br/",
    )

    result = run_hreflang_audit([en, pt])

    assert "hreflang.missing_reciprocal" not in _finding_ids(result)


def test_reciprocal_link_missing_generates_finding():
    en = extract_hreflang_from_html(
        """
        <head>
          <link rel="alternate" hreflang="en" href="https://example.com/en/">
          <link rel="alternate" hreflang="pt-BR" href="https://example.com/pt-br/">
        </head>
        """,
        "https://example.com/en/",
    )
    pt = extract_hreflang_from_html(
        '<head><link rel="alternate" hreflang="pt-BR" href="https://example.com/pt-br/"></head>',
        "https://example.com/pt-br/",
    )

    result = run_hreflang_audit([en, pt])
    finding = _finding_by_id(result, "hreflang.missing_reciprocal")

    assert finding.page_url == "https://example.com/en/"
    assert result.summary.missing_reciprocal_links == 1


def test_x_default_info_behavior_is_optional():
    page = extract_hreflang_from_html(
        '<head><link rel="alternate" hreflang="en" href="https://example.com/en/"></head>',
        "https://example.com/en/",
    )

    default_result = run_hreflang_audit([page])
    noisy_result = run_hreflang_audit([page], options=HreflangAuditOptions(flag_missing_x_default=True))

    assert "hreflang.missing_x_default" not in _finding_ids(default_result)
    assert _finding_by_id(noisy_result, "hreflang.missing_x_default").severity == "info"


def test_summary_counts_pages_site_metrics_and_findings():
    en = extract_hreflang_from_html(
        """
        <head>
          <link rel="alternate" hreflang="en" href="https://example.com/en/">
          <link rel="alternate" hreflang="pt_BR" href="/pt-br/">
          <link rel="alternate" hreflang="x-default" href="https://example.com/">
          <link rel="alternate" hreflang="fr" href="https://example.fr/fr/">
        </head>
        """,
        "https://example.com/en/",
        allowed_hosts=["example.com"],
    )

    result = run_hreflang_audit([en], start_url="https://example.com/en/")

    assert result.start_url == "https://example.com/en/"
    assert result.summary.total_pages == 1
    assert result.summary.total_links == 4
    assert result.summary.findings_total == len(result.findings)
    assert result.summary.pages_with_x_default == 1
    assert result.summary.invalid_hreflang_links == 1
    assert result.summary.relative_url_links == 1
    assert result.summary.external_url_links == 1
    assert result.summary.by_severity
    assert result.summary.by_category


def test_output_is_json_serializable():
    page = extract_hreflang_from_html(
        '<head><link rel="alternate" hreflang="en" href="https://example.com/en/"></head>',
        "https://example.com/en/",
    )
    result = run_hreflang_audit([page])

    rendered = json.dumps(result.model_dump(mode="json"), sort_keys=True)

    assert "summary" in rendered


def _finding_ids(result):
    return [finding.id for finding in result.findings]


def _finding_by_id(result, finding_id):
    return next(finding for finding in result.findings if finding.id == finding_id)
