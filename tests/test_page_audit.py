import httpx

from geo_seo_engine.analyzers.page_audit import audit_page
from geo_seo_engine.http import HttpClient, HttpClientConfig


def test_audit_page_extracts_basic_metadata():
    html = '''
    <html>
      <head>
        <title>Example Title</title>
        <meta name="description" content="Example description">
        <link rel="canonical" href="https://example.com/page">
      </head>
      <body>
        <h1>Main Heading</h1>
        <a href="/internal">Internal</a>
        <a href="https://external.com">External</a>
      </body>
    </html>
    '''

    def handler(request):
        return httpx.Response(
            200,
            text=html,
            headers={"content-type": "text/html"},
            request=request,
        )

    client = HttpClient(
        HttpClientConfig(retries=0),
        transport=httpx.MockTransport(handler),
    )

    result = audit_page("https://example.com/page", http_client=client)

    assert result.status_code == 200
    assert result.title == "Example Title"
    assert result.meta_description == "Example description"
    assert result.h1 == ["Main Heading"]
    assert result.canonical == "https://example.com/page"
    assert result.internal_links == 1
    assert result.external_links == 1
    assert result.issues == []
