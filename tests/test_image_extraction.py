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
