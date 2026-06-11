import httpx

from geo_seo_engine.analyzers.robots_audit import audit_robots


def test_audit_robots_extracts_directives(monkeypatch):
    robots = '''
    User-agent: *
    Disallow: /admin
    Allow: /blog
    Sitemap: https://example.com/sitemap.xml
    '''

    def fake_get(*args, **kwargs):
        return httpx.Response(
            200,
            text=robots,
            headers={"content-type": "text/plain"},
            request=httpx.Request("GET", "https://example.com/robots.txt"),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = audit_robots("https://example.com")

    assert result.status_code == 200
    assert result.user_agents == ["*"]
    assert result.allow_count == 1
    assert result.disallow_count == 1
    assert result.sitemap_urls == ["https://example.com/sitemap.xml"]
    assert result.blocks_all is False
    assert result.issues == []


def test_audit_robots_detects_disallow_all(monkeypatch):
    robots = '''
    User-agent: *
    Disallow: /
    '''

    def fake_get(*args, **kwargs):
        return httpx.Response(
            200,
            text=robots,
            headers={"content-type": "text/plain"},
            request=httpx.Request("GET", "https://example.com/robots.txt"),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = audit_robots("https://example.com/robots.txt")

    assert result.blocks_all is True
    assert "disallow_all_found" in result.issues
    assert "missing_sitemap_directive" in result.issues


def test_audit_robots_does_not_parse_404_html_body(monkeypatch):
    html = '<!doctype html><html><head><title>Not Found</title></head></html>'

    def fake_get(*args, **kwargs):
        return httpx.Response(
            404,
            text=html,
            headers={"content-type": "text/html"},
            request=httpx.Request("GET", "https://example.com/robots.txt"),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = audit_robots("https://example.com/robots.txt")

    assert result.status_code == 404
    assert result.line_count == 0
    assert result.unknown_directives == []
    assert result.user_agents == []
    assert result.issues == [
        "status_code_not_200: 404",
        "robots_txt_4xx_assumed_no_restrictions",
    ]
