import geo_seo_engine.i18n.extract as hreflang_extract

from geo_seo_engine.i18n import extract_hreflang_from_html


def test_extracts_valid_hreflang_values_and_x_default():
    result = extract_hreflang_from_html(
        """
        <html><head>
          <link rel="alternate" hreflang="en" href="https://example.com/en/">
          <link rel="alternate" hreflang="pt-br" href="https://example.com/pt-br/">
          <link rel="alternate" hreflang="es-ES" href="https://example.com/es-es/">
          <link rel="alternate" hreflang="x-default" href="https://example.com/">
        </head></html>
        """,
        "https://example.com/en/",
    )

    assert [link.normalized_hreflang for link in result.links] == ["en", "pt-BR", "es-ES", "x-default"]
    assert result.links[-1].is_x_default is True
    assert all(not link.is_invalid_hreflang for link in result.links)


def test_rejects_country_only_hreflang():
    result = extract_hreflang_from_html(
        '<head><link rel="alternate" hreflang="BR" href="https://example.com/br/"></head>',
        "https://example.com/",
    )

    assert result.links[0].is_invalid_hreflang is True
    assert result.links[0].normalized_hreflang is None


def test_rejects_underscore_hreflang():
    result = extract_hreflang_from_html(
        '<head><link rel="alternate" hreflang="pt_BR" href="https://example.com/pt-br/"></head>',
        "https://example.com/",
    )

    assert result.links[0].is_invalid_hreflang is True


def test_registers_missing_href_and_hreflang():
    result = extract_hreflang_from_html(
        """
        <head>
          <link rel="alternate" hreflang="en">
          <link rel="alternate" href="https://example.com/pt-br/">
        </head>
        """,
        "https://example.com/",
    )

    assert result.links == []
    assert [skipped.reason for skipped in result.skipped_links] == ["missing_href", "missing_hreflang"]


def test_resolves_relative_href_and_flags_it():
    result = extract_hreflang_from_html(
        '<head><link rel="alternate" hreflang="pt-BR" href="/pt-br/"></head>',
        "https://example.com/en/",
    )

    assert result.links[0].resolved_url == "https://example.com/pt-br/"
    assert result.links[0].normalized_url == "https://example.com/pt-br/"
    assert result.links[0].is_relative is True


def test_detects_invalid_url_and_non_http_url():
    result = extract_hreflang_from_html(
        """
        <head>
          <link rel="alternate" hreflang="en" href="https://exa mple.com/en/">
          <link rel="alternate" hreflang="pt-BR" href="mailto:pt@example.com">
        </head>
        """,
        "https://example.com/",
    )

    assert [link.is_invalid_url for link in result.links] == [True, True]
    assert result.links[1].is_non_http is True


def test_detects_duplicate_hreflang_value():
    result = extract_hreflang_from_html(
        """
        <head>
          <link rel="alternate" hreflang="en" href="https://example.com/en/">
          <link rel="alternate" hreflang="EN-us" href="https://example.com/en-us/">
          <link rel="alternate" hreflang="en-US" href="https://example.com/us/">
        </head>
        """,
        "https://example.com/en/",
    )

    assert result.duplicates == {"en-US": 2}


def test_detects_external_host_signal():
    result = extract_hreflang_from_html(
        '<head><link rel="alternate" hreflang="fr" href="https://example.fr/fr/"></head>',
        "https://example.com/",
        allowed_hosts=["example.com"],
    )

    assert result.links[0].is_external is True


def test_ignores_alternate_links_outside_head():
    result = extract_hreflang_from_html(
        '<body><link rel="alternate" hreflang="en" href="https://example.com/en/"></body>',
        "https://example.com/",
    )

    assert result.links == []


def test_extraction_does_not_perform_network_calls(monkeypatch):
    def fail_fetch(*args, **kwargs):
        raise AssertionError("network should not be used")

    monkeypatch.setattr(hreflang_extract, "resolve_url", hreflang_extract.resolve_url)

    result = extract_hreflang_from_html(
        '<head><link rel="alternate" hreflang="en" href="https://example.com/en/"></head>',
        "https://example.com/",
    )

    assert result.links[0].normalized_url == "https://example.com/en/"
    assert callable(fail_fetch)
