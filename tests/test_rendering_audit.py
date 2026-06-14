import json

from geo_seo_engine.rendering import RenderingAuditOptions, extract_render_snapshot, run_rendering_audit


def test_run_rendering_audit_flags_title_description_canonical_and_robots_changes():
    page = extract_render_snapshot(
        "https://example.com/",
        """
        <html><head>
          <title>Static</title>
          <meta name="description" content="Static description">
          <link rel="canonical" href="https://example.com/static">
          <meta name="robots" content="index,follow">
        </head><body>Static body text</body></html>
        """,
        """
        <html><head>
          <title>Rendered</title>
          <meta name="description" content="Rendered description">
          <link rel="canonical" href="https://example.com/rendered">
          <meta name="robots" content="noindex,follow">
        </head><body>Rendered body text</body></html>
        """,
    )

    result = run_rendering_audit([page], start_url="https://example.com/")
    ids = {finding.id for finding in result.findings}

    assert "rendering.title_changed" in ids
    assert "rendering.meta_description_changed" in ids
    assert "rendering.canonical_changed" in ids
    assert "rendering.robots_changed" in ids
    assert "rendering.rendered_noindex" in ids
    assert result.summary.pages_title_changed == 1
    assert result.summary.pages_description_changed == 1
    assert result.summary.pages_canonical_changed == 1
    assert result.summary.pages_robots_changed == 1


def test_run_rendering_audit_flags_links_added_by_js():
    page = extract_render_snapshot(
        "https://example.com/",
        "<html><body><a href='/one'>One</a></body></html>",
        """
        <html><body>
          <a href='/one'>One</a><a href='/two'>Two</a><a href='/three'>Three</a><a href='/four'>Four</a>
        </body></html>
        """,
    )

    result = run_rendering_audit([page])

    assert [finding.id for finding in result.findings] == ["rendering.links_added_by_js"]
    assert result.summary.pages_links_added_by_js == 1


def test_run_rendering_audit_flags_sparse_static_and_rendered_content():
    rendered_text = " ".join(["rendered content"] * 40)
    page = extract_render_snapshot(
        "https://example.com/app",
        "<html><body><div id='app'></div><script src='/app.js'></script></body></html>",
        f"<html><body><main>{rendered_text}</main></body></html>",
    )

    result = run_rendering_audit([page])
    ids = {finding.id for finding in result.findings}

    assert "rendering.static_content_sparse" in ids
    assert "rendering.content_only_after_render" in ids
    assert result.summary.pages_static_sparse_rendered_content == 1


def test_run_rendering_audit_flags_render_error_and_serializes_json():
    page = extract_render_snapshot(
        "https://example.com/",
        "<html><body>Static</body></html>",
        render_error="render timed out",
        render_status="timeout",
    )

    result = run_rendering_audit([page], options=RenderingAuditOptions(), start_url="https://example.com/")
    rendered = json.dumps(result.model_dump(mode="json"), sort_keys=True)

    assert result.findings[0].id == "rendering.render_error"
    assert result.summary.render_errors == 1
    assert "rendering.render_error" in rendered
