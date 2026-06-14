from geo_seo_engine.rendering import extract_render_snapshot


def test_extract_render_snapshot_compares_static_and_rendered_signals():
    static_html = """
    <html>
      <head>
        <title>Static title</title>
        <meta name="description" content="Static description">
        <link rel="canonical" href="/static">
        <meta name="robots" content="index,follow">
      </head>
      <body><a href="/one">One</a><script>window.app = true</script>Static text</body>
    </html>
    """
    rendered_html = """
    <html>
      <head>
        <title>Rendered title</title>
        <meta name="description" content="Rendered description">
        <link rel="canonical" href="/rendered">
        <meta name="robots" content="noindex,follow">
      </head>
      <body><a href="/one">One</a><a href="/two">Two</a>Rendered text</body>
    </html>
    """

    snapshot = extract_render_snapshot("https://example.com/page", static_html, rendered_html)

    assert snapshot.static_title == "Static title"
    assert snapshot.rendered_title == "Rendered title"
    assert snapshot.static_meta_description == "Static description"
    assert snapshot.rendered_meta_description == "Rendered description"
    assert snapshot.static_canonical == "https://example.com/static"
    assert snapshot.rendered_canonical == "https://example.com/rendered"
    assert snapshot.static_robots == "index,follow"
    assert snapshot.rendered_robots == "noindex,follow"
    assert snapshot.static_links == ["https://example.com/one"]
    assert snapshot.rendered_links == ["https://example.com/one", "https://example.com/two"]
    assert snapshot.static_script_count == 1


def test_extract_render_snapshot_records_render_error_without_rendered_html():
    snapshot = extract_render_snapshot(
        "https://example.com/",
        "<html><head><title>Static</title></head></html>",
        render_error="timeout",
        render_status="timeout",
    )

    assert snapshot.render_status == "timeout"
    assert snapshot.render_error == "timeout"
    assert snapshot.rendered_title is None
    assert snapshot.rendered_links == []
