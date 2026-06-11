import httpx

from geo_seo_engine.analyzers.structured_data_audit import (
    audit_structured_data,
    audit_structured_data_html,
)
from geo_seo_engine.http import HttpClient, HttpClientConfig


def test_audit_structured_data_reports_missing_when_no_json_ld():
    result = audit_structured_data_html("<html><head></head><body></body></html>")

    assert result.json_ld_blocks == 0
    assert result.types == []
    assert result.issues == ["missing"]


def test_audit_structured_data_extracts_valid_json_ld_types():
    html = """
    <script type="application/ld+json">
      {"@context": "https://schema.org", "@type": "Article"}
    </script>
    <script type="application/ld+json">
      {"@context": "https://schema.org", "@type": ["Organization", "LocalBusiness"]}
    </script>
    """

    result = audit_structured_data_html(html)

    assert result.json_ld_blocks == 2
    assert result.valid_json_ld_blocks == 2
    assert result.invalid_json_ld_blocks == 0
    assert result.types == ["Article", "Organization", "LocalBusiness"]
    assert result.issues == []


def test_audit_structured_data_reports_invalid_json_ld():
    html = """
    <script type="application/ld+json">
      {"@context": "https://schema.org", "@type": "Article"
    </script>
    """

    result = audit_structured_data_html(html)

    assert result.json_ld_blocks == 1
    assert result.valid_json_ld_blocks == 0
    assert result.invalid_json_ld_blocks == 1
    assert result.blocks[0].valid is False
    assert result.issues == ["invalid_json_ld"]


def test_audit_structured_data_reports_missing_type():
    html = """
    <script type="application/ld+json">
      {"@context": "https://schema.org", "name": "Example"}
    </script>
    """

    result = audit_structured_data_html(html)

    assert result.json_ld_blocks == 1
    assert result.valid_json_ld_blocks == 1
    assert result.types == []
    assert result.issues == ["missing_type"]


def test_audit_structured_data_uses_injected_http_client():
    html = """
    <script type="application/ld+json">
      {"@context": "https://schema.org", "@type": "WebPage"}
    </script>
    """
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text=html, request=request)
    )
    client = HttpClient(HttpClientConfig(retries=0), transport=transport)

    result = audit_structured_data("https://example.com/page", http_client=client)

    assert result.json_ld_blocks == 1
    assert result.types == ["WebPage"]
    assert result.issues == []
