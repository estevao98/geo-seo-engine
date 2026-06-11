import httpx

from geo_seo_engine.analyzers.sitemap_audit import audit_sitemap


def test_audit_sitemap_urlset_extracts_urls(monkeypatch):
    xml = '''
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://example.com/</loc>
        <lastmod>2026-06-10</lastmod>
      </url>
      <url>
        <loc>https://example.com/blog?utm_source=x</loc>
      </url>
    </urlset>
    '''

    def fake_get(*args, **kwargs):
        return httpx.Response(
            200,
            content=xml.encode("utf-8"),
            headers={"content-type": "application/xml"},
            request=httpx.Request("GET", "https://example.com/sitemap.xml"),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = audit_sitemap("https://example.com/sitemap.xml")

    assert result.status_code == 200
    assert result.sitemap_type == "urlset"
    assert result.url_count == 2
    assert result.missing_lastmod_count == 1
    assert result.urls_with_query == ["https://example.com/blog?utm_source=x"]
    assert "urls_with_query_found" in result.issues


def test_audit_sitemap_detects_sitemapindex(monkeypatch):
    xml = '''
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap>
        <loc>https://example.com/sitemap-posts.xml</loc>
      </sitemap>
    </sitemapindex>
    '''

    def fake_get(*args, **kwargs):
        return httpx.Response(
            200,
            content=xml.encode("utf-8"),
            headers={"content-type": "application/xml"},
            request=httpx.Request("GET", "https://example.com/sitemap.xml"),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = audit_sitemap("https://example.com/sitemap.xml")

    assert result.sitemap_type == "sitemapindex"
    assert result.url_count == 1
    assert result.urls[0].loc == "https://example.com/sitemap-posts.xml"
