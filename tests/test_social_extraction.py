import geo_seo_engine.social.extract as social_extract

from geo_seo_engine.social import extract_social_metadata_from_html


def test_extracts_open_graph_metadata():
    result = extract_social_metadata_from_html(
        """
        <meta property="og:title" content="Title">
        <meta property="og:description" content="Description">
        <meta property="og:image" content="https://example.com/og.png">
        <meta property="og:url" content="https://example.com/page">
        <meta property="og:type" content="article">
        <meta property="og:site_name" content="Example">
        <meta property="og:locale" content="en_US">
        """,
        "https://example.com/page",
    )

    assert result.open_graph == {
        "og:title": "Title",
        "og:description": "Description",
        "og:image": "https://example.com/og.png",
        "og:url": "https://example.com/page",
        "og:type": "article",
        "og:site_name": "Example",
        "og:locale": "en_US",
    }
    assert result.tags[0].kind == "og"
    assert result.tags[0].attribute_name == "property"


def test_extracts_twitter_metadata():
    result = extract_social_metadata_from_html(
        """
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="Title">
        <meta name="twitter:description" content="Description">
        <meta name="twitter:image" content="https://example.com/twitter.png">
        <meta name="twitter:site" content="@site">
        <meta name="twitter:creator" content="@creator">
        """,
        "https://example.com/page",
    )

    assert result.twitter == {
        "twitter:card": "summary_large_image",
        "twitter:title": "Title",
        "twitter:description": "Description",
        "twitter:image": "https://example.com/twitter.png",
        "twitter:site": "@site",
        "twitter:creator": "@creator",
    }
    assert result.tags[0].kind == "twitter"
    assert result.tags[0].attribute_name == "name"


def test_detects_empty_content():
    result = extract_social_metadata_from_html(
        '<meta property="og:title" content="  ">',
        "https://example.com/page",
    )

    assert result.tags[0].content == ""
    assert result.tags[0].is_empty is True
    assert result.open_graph["og:title"] == ""


def test_detects_duplicate_tags():
    result = extract_social_metadata_from_html(
        """
        <meta property="og:title" content="First">
        <meta property="og:title" content="Second">
        <meta name="twitter:card" content="summary">
        <meta name="twitter:card" content="summary_large_image">
        """,
        "https://example.com/page",
    )

    assert result.duplicates == {"og:title": 2, "twitter:card": 2}
    assert result.open_graph["og:title"] == "First"


def test_detects_relative_social_image_url():
    result = extract_social_metadata_from_html(
        '<meta property="og:image" content="/images/social.png">',
        "https://example.com/page",
    )

    image = result.image_references[0]
    assert image.is_relative is True
    assert image.is_invalid is False
    assert image.resolved_url == "https://example.com/images/social.png"
    assert image.normalized_url == "https://example.com/images/social.png"


def test_detects_invalid_social_image_url():
    result = extract_social_metadata_from_html(
        '<meta property="og:image" content="https://exa mple.com/social.png">',
        "https://example.com/page",
    )

    image = result.image_references[0]
    assert image.is_invalid is True
    assert image.normalized_url is None


def test_invalid_social_image_url_does_not_break_on_parse_error():
    result = extract_social_metadata_from_html(
        '<meta property="og:image" content="https://[::1/social.png">',
        "https://example.com/page",
    )

    assert result.image_references[0].is_invalid is True


def test_detects_data_uri_social_image_without_normalizing(monkeypatch):
    def fail_normalize_url(url: str):
        raise AssertionError(f"normalize_url should not be called for data URI: {url}")

    monkeypatch.setattr(social_extract, "normalize_url", fail_normalize_url)

    result = extract_social_metadata_from_html(
        '<meta property="og:image" content="data:image/png;base64,AAAA">',
        "https://example.com/page",
    )

    image = result.image_references[0]
    assert image.is_data_uri is True
    assert image.is_invalid is True


def test_detects_external_social_image_host():
    result = extract_social_metadata_from_html(
        '<meta property="og:image" content="https://cdn.example.net/social.png">',
        "https://example.com/page",
        allowed_hosts=["example.com"],
    )

    assert result.image_references[0].is_external is True
