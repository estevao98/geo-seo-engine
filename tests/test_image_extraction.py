import geo_seo_engine.images.extract as image_extract

from geo_seo_engine.images import extract_images_from_html


def test_extracts_relative_image_src():
    result = extract_images_from_html(
        '<img src="/images/logo.png" alt="Logo">',
        "https://example.com/docs/page",
    )

    assert result.images[0].raw_src == "/images/logo.png"
    assert result.images[0].resolved_src == "https://example.com/images/logo.png"
    assert result.images[0].normalized_src == "https://example.com/images/logo.png"


def test_extracts_absolute_image_src():
    result = extract_images_from_html(
        '<img src="https://example.com/images/hero.jpg" alt="Hero">',
        "https://example.com/",
    )

    assert result.images[0].resolved_src == "https://example.com/images/hero.jpg"
    assert result.images[0].normalized_src == "https://example.com/images/hero.jpg"


def test_extracts_protocol_relative_image_src():
    result = extract_images_from_html(
        '<img src="//example.com/images/hero.jpg" alt="Hero">',
        "https://example.com/",
    )

    assert result.images[0].resolved_src == "https://example.com/images/hero.jpg"
    assert result.images[0].normalized_src == "https://example.com/images/hero.jpg"


def test_registers_missing_src():
    result = extract_images_from_html("<img alt='Missing source'>", "https://example.com/")

    assert result.images == []
    assert result.skipped_images[0].reason == "missing_src"
    assert result.skipped_images[0].raw_src is None


def test_distinguishes_missing_alt_from_empty_alt():
    result = extract_images_from_html(
        """
        <img src="/missing-alt.png">
        <img src="/empty-alt.png" alt="">
        """,
        "https://example.com/",
    )

    missing_alt, empty_alt = result.images
    assert missing_alt.has_alt_attribute is False
    assert missing_alt.alt is None
    assert empty_alt.has_alt_attribute is True
    assert empty_alt.alt == ""
    assert empty_alt.is_decorative is False


def test_distinguishes_decorative_empty_alt():
    result = extract_images_from_html(
        """
        <img src="/icon.svg" alt="" role="presentation">
        <img src="/hidden.svg" alt="" aria-hidden="true">
        """,
        "https://example.com/",
    )

    assert [image.has_alt_attribute for image in result.images] == [True, True]
    assert [image.alt for image in result.images] == ["", ""]
    assert [image.is_decorative for image in result.images] == [True, True]


def test_preserves_width_and_height():
    result = extract_images_from_html(
        '<img src="/image.png" alt="Image" width="640" height="480">',
        "https://example.com/",
    )

    assert result.images[0].width == "640"
    assert result.images[0].height == "480"


def test_preserves_loading_lazy():
    result = extract_images_from_html(
        '<img src="/image.png" alt="Image" loading="lazy">',
        "https://example.com/",
    )

    assert result.images[0].loading == "lazy"


def test_preserves_srcset():
    result = extract_images_from_html(
        '<img src="/image.png" srcset="/image.png 1x, /image@2x.png 2x" alt="Image">',
        "https://example.com/",
    )

    assert result.images[0].srcset == "/image.png 1x, /image@2x.png 2x"


def test_parses_img_srcset_candidates_without_normalizing_descriptors():
    result = extract_images_from_html(
        '<img src="/image.png" srcset="/small.jpg 480w,  /large.jpg 960w, /retina.jpg 2x" alt="Image">',
        "https://example.com/",
    )

    assert [(candidate.raw_url, candidate.descriptor) for candidate in result.images[0].srcset_candidates] == [
        ("/small.jpg", "480w"),
        ("/large.jpg", "960w"),
        ("/retina.jpg", "2x"),
    ]


def test_picture_source_srcset_does_not_break_image_extraction():
    result = extract_images_from_html(
        """
        <picture>
          <source srcset="/hero.avif 1x, /hero@2x.avif 2x" type="image/avif">
          <img src="/hero.jpg" alt="Hero">
        </picture>
        """,
        "https://example.com/",
    )

    assert len(result.images) == 1
    assert result.images[0].normalized_src == "https://example.com/hero.jpg"


def test_detects_external_image_host():
    result = extract_images_from_html(
        '<img src="https://cdn.example.net/image.png" alt="CDN">',
        "https://example.com/",
        allowed_hosts=["example.com"],
    )

    assert result.images[0].is_external is True


def test_detects_data_uri():
    result = extract_images_from_html(
        '<img src="data:image/png;base64,AAAA" alt="Inline">',
        "https://example.com/",
    )

    assert result.images[0].is_data_uri is True
    assert result.images[0].resolved_src == "data:image/png;base64,AAAA"
    assert result.images[0].normalized_src == "data:image/png;base64,AAAA"


def test_data_uri_does_not_call_url_normalization(monkeypatch):
    def fail_normalize_url(url: str):
        raise AssertionError(f"normalize_url should not be called for data URI: {url}")

    monkeypatch.setattr(image_extract, "normalize_url", fail_normalize_url)

    result = extract_images_from_html(
        '<img src="data:image/png;base64,AAAA" alt="Inline">',
        "https://example.com/",
    )

    assert result.images[0].is_data_uri is True
