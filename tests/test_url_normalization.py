from __future__ import annotations

import pytest

from geo_seo_engine.core import (
    UrlNormalizationOptions,
    is_same_site,
    normalize_url,
    resolve_url,
    url_host,
)


def test_normalizes_simple_absolute_url():
    result = normalize_url("https://example.com/path")

    assert result.raw_url == "https://example.com/path"
    assert result.normalized_url == "https://example.com/path"
    assert result.host == "example.com"
    assert result.path == "/path"
    assert result.query == ""


def test_url_without_path_becomes_slash():
    result = normalize_url("https://example.com")

    assert result.normalized_url == "https://example.com/"
    assert result.path == "/"


def test_uppercase_scheme_and_host_become_lowercase():
    result = normalize_url("HTTPS://EXAMPLE.COM/Path")

    assert result.normalized_url == "https://example.com/Path"
    assert result.host == "example.com"


def test_path_keeps_original_case():
    result = normalize_url("https://example.com/Products/SEO")

    assert result.path == "/Products/SEO"
    assert result.normalized_url == "https://example.com/Products/SEO"


def test_fragment_is_removed_by_default():
    result = normalize_url("https://example.com/a#section")

    assert result.normalized_url == "https://example.com/a"
    assert result.removed_fragment == "section"


def test_query_is_preserved_by_default():
    result = normalize_url("https://example.com/a?b=2&a=1")

    assert result.normalized_url == "https://example.com/a?b=2&a=1"
    assert result.query == "b=2&a=1"


def test_query_can_be_sorted():
    result = normalize_url(
        "https://example.com/a?b=2&a=1",
        options=UrlNormalizationOptions(sort_query_params=True),
    )

    assert result.normalized_url == "https://example.com/a?a=1&b=2"
    assert result.query == "a=1&b=2"


def test_tracking_params_are_preserved_by_default():
    result = normalize_url("https://example.com/a?utm_source=x&id=1&fbclid=y")

    assert result.normalized_url == "https://example.com/a?utm_source=x&id=1&fbclid=y"


def test_tracking_params_can_be_removed():
    result = normalize_url(
        "https://example.com/a?utm_source=x&id=1&fbclid=y",
        options=UrlNormalizationOptions(remove_tracking_params=True),
    )

    assert result.normalized_url == "https://example.com/a?id=1"
    assert result.query == "id=1"


@pytest.mark.parametrize(
    ("raw_url", "expected"),
    [
        ("http://example.com:80/a", "http://example.com/a"),
        ("https://example.com:443/a", "https://example.com/a"),
    ],
)
def test_default_port_is_removed(raw_url, expected):
    assert normalize_url(raw_url).normalized_url == expected


def test_non_default_port_is_preserved():
    result = normalize_url("https://example.com:8443/a")

    assert result.normalized_url == "https://example.com:8443/a"


def test_relative_url_is_resolved_with_base_url():
    result = normalize_url("../b", base_url="https://example.com/a/page")

    assert result.base_url == "https://example.com/a/page"
    assert result.normalized_url == "https://example.com/b"


def test_protocol_relative_url_is_resolved_with_base_url():
    assert resolve_url("//example.com/path", "https://example.com/base") == "https://example.com/path"
    result = normalize_url("//EXAMPLE.com/path", base_url="https://example.com/base")
    assert result.normalized_url == "https://example.com/path"


def test_trailing_slash_is_not_removed_by_default():
    result = normalize_url("https://example.com/a/")
    assert result.normalized_url == "https://example.com/a/"


def test_trailing_slash_can_be_removed_except_root():
    options = UrlNormalizationOptions(strip_trailing_slash=True)

    result = normalize_url("https://example.com/a/", options=options)

    assert result.normalized_url == "https://example.com/a"
    assert normalize_url("https://example.com/", options=options).normalized_url == "https://example.com/"


@pytest.mark.parametrize(
    "raw_url",
    [
        "mailto:test@example.com",
        "tel:+551199999999",
        "javascript:alert(1)",
        "data:text/plain,test",
        "ftp://example.com/a",
    ],
)
def test_unsupported_schemes_are_rejected(raw_url):
    with pytest.raises(ValueError, match="http or https"):
        normalize_url(raw_url)


@pytest.mark.parametrize("raw_url", ["", "not-a-url", "https://", "https://example.com:bad/a"])
def test_invalid_url_raises_clear_value_error(raw_url):
    with pytest.raises(ValueError) as error:
        normalize_url(raw_url)

    message = str(error.value)
    assert "URL" in message or "raw_url" in message


def test_is_same_site_accepts_allowed_host():
    assert is_same_site("https://example.com/a", ["example.com"])


def test_is_same_site_rejects_external_host():
    assert not is_same_site("https://other.example/a", ["example.com"])


def test_allowed_hosts_are_case_insensitive():
    assert is_same_site("https://Example.com/a", ["EXAMPLE.COM"])


def test_url_host_returns_hostname_or_none():
    assert url_host("https://EXAMPLE.com:443/a") == "example.com"
    assert url_host("not-a-url") is None
