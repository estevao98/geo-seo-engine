from __future__ import annotations

from geo_seo_engine.crawler import CrawlOptions, crawl_site
from geo_seo_engine.http import FetchResult


class FakeHttpClient:
    def __init__(self, responses: dict[str, FetchResult]) -> None:
        self.responses = responses
        self.requested_urls: list[str] = []

    def fetch(self, url: str) -> FetchResult:
        self.requested_urls.append(url)
        return self.responses.get(
            url,
            FetchResult(
                url=url,
                final_url=url,
                status_code=0,
                error="missing fake response",
            ),
        )


def html_response(url: str, html: str) -> FetchResult:
    return FetchResult(
        url=url,
        final_url=url,
        status_code=200,
        content_type="text/html; charset=utf-8",
        text=html,
    )


def test_crawler_visits_start_url():
    client = FakeHttpClient({"https://example.com/": html_response("https://example.com/", "")})

    result = crawl_site("https://example.com", http_client=client)

    assert client.requested_urls == ["https://example.com/"]
    assert result.pages[0].normalized_url == "https://example.com/"
    assert result.pages[0].depth == 0


def test_crawler_extracts_relative_internal_link():
    client = FakeHttpClient(
        {
            "https://example.com/": html_response(
                "https://example.com/",
                '<a href="/about">About us</a>',
            ),
            "https://example.com/about": html_response("https://example.com/about", ""),
        }
    )

    result = crawl_site("https://example.com", http_client=client)

    assert client.requested_urls == ["https://example.com/", "https://example.com/about"]
    assert result.discovered_urls[0].raw_href == "/about"
    assert result.discovered_urls[0].anchor_text == "About us"
    assert result.discovered_urls[0].normalized_url == "https://example.com/about"


def test_crawler_resolves_protocol_relative_url():
    client = FakeHttpClient(
        {
            "https://example.com/": html_response(
                "https://example.com/",
                '<a href="//example.com/path">Path</a>',
            ),
            "https://example.com/path": html_response("https://example.com/path", ""),
        }
    )

    result = crawl_site("https://example.com", http_client=client)

    assert result.discovered_urls[0].resolved_url == "https://example.com/path"
    assert client.requested_urls == ["https://example.com/", "https://example.com/path"]


def test_crawler_ignores_external_links():
    client = FakeHttpClient(
        {
            "https://example.com/": html_response(
                "https://example.com/",
                '<a href="https://other.example/page">External</a>',
            ),
        }
    )

    result = crawl_site("https://example.com", http_client=client)

    assert client.requested_urls == ["https://example.com/"]
    assert result.discovered_urls == []
    assert result.skipped_urls[0].reason == "external_host"


def test_crawler_ignores_unsupported_link_schemes():
    client = FakeHttpClient(
        {
            "https://example.com/": html_response(
                "https://example.com/",
                """
                <a href="mailto:test@example.com">Mail</a>
                <a href="tel:+551199999999">Phone</a>
                <a href="javascript:alert(1)">JS</a>
                <a href="data:text/plain,test">Data</a>
                """,
            ),
        }
    )

    result = crawl_site("https://example.com", http_client=client)

    assert result.discovered_urls == []
    assert [skip.reason for skip in result.skipped_urls] == [
        "unsupported_scheme:mailto",
        "unsupported_scheme:tel",
        "unsupported_scheme:javascript",
        "unsupported_scheme:data",
    ]


def test_crawler_deduplicates_normalized_urls():
    client = FakeHttpClient(
        {
            "https://example.com/": html_response(
                "https://example.com/",
                """
                <a href="/a#section">A fragment</a>
                <a href="https://EXAMPLE.com/a">A uppercase host</a>
                """,
            ),
            "https://example.com/a": html_response("https://example.com/a", ""),
        }
    )

    result = crawl_site("https://example.com", http_client=client)

    assert client.requested_urls == ["https://example.com/", "https://example.com/a"]
    assert [link.normalized_url for link in result.discovered_urls] == ["https://example.com/a"]
    assert any(skip.reason == "duplicate_normalized_url" for skip in result.skipped_urls)


def test_crawler_respects_max_pages():
    client = FakeHttpClient(
        {
            "https://example.com/": html_response(
                "https://example.com/",
                '<a href="/a">A</a><a href="/b">B</a>',
            ),
            "https://example.com/a": html_response("https://example.com/a", ""),
            "https://example.com/b": html_response("https://example.com/b", ""),
        }
    )

    result = crawl_site(
        "https://example.com",
        options=CrawlOptions(max_pages=2, max_depth=2),
        http_client=client,
    )

    assert client.requested_urls == ["https://example.com/", "https://example.com/a"]
    assert len(result.pages) == 2
    assert result.max_pages_reached is True


def test_crawler_respects_max_depth():
    client = FakeHttpClient(
        {
            "https://example.com/": html_response(
                "https://example.com/",
                '<a href="/a">A</a>',
            ),
            "https://example.com/a": html_response(
                "https://example.com/a",
                '<a href="/b">B</a>',
            ),
            "https://example.com/b": html_response("https://example.com/b", ""),
        }
    )

    result = crawl_site(
        "https://example.com",
        options=CrawlOptions(max_depth=1),
        http_client=client,
    )

    assert client.requested_urls == ["https://example.com/", "https://example.com/a"]
    assert any(skip.url == "https://example.com/b" for skip in result.skipped_urls)
    assert any(skip.reason == "max_depth_exceeded" for skip in result.skipped_urls)


def test_crawler_respects_exclude_patterns():
    client = FakeHttpClient(
        {
            "https://example.com/": html_response(
                "https://example.com/",
                '<a href="/keep">Keep</a><a href="/private/page">Private</a>',
            ),
            "https://example.com/keep": html_response("https://example.com/keep", ""),
        }
    )

    result = crawl_site(
        "https://example.com",
        options=CrawlOptions(exclude_patterns=["/private/*"]),
        http_client=client,
    )

    assert client.requested_urls == ["https://example.com/", "https://example.com/keep"]
    assert [link.normalized_url for link in result.discovered_urls] == ["https://example.com/keep"]
    assert any(skip.reason == "excluded_by_pattern" for skip in result.skipped_urls)


def test_crawler_respects_include_patterns():
    client = FakeHttpClient(
        {
            "https://example.com/": html_response(
                "https://example.com/",
                '<a href="/blog/post">Post</a><a href="/docs/page">Docs</a>',
            ),
            "https://example.com/blog/post": html_response("https://example.com/blog/post", ""),
        }
    )

    result = crawl_site(
        "https://example.com",
        options=CrawlOptions(include_patterns=["/blog/*"]),
        http_client=client,
    )

    assert client.requested_urls == ["https://example.com/", "https://example.com/blog/post"]
    assert [link.normalized_url for link in result.discovered_urls] == ["https://example.com/blog/post"]
    assert any(skip.reason == "not_included_by_pattern" for skip in result.skipped_urls)


def test_crawler_records_fetch_error():
    client = FakeHttpClient(
        {
            "https://example.com/": FetchResult(
                url="https://example.com/",
                final_url="https://example.com/",
                status_code=0,
                error="request_error: connection failed",
            )
        }
    )

    result = crawl_site("https://example.com", http_client=client)

    assert result.pages[0].error == "request_error: connection failed"
    assert result.errors == ["https://example.com/: request_error: connection failed"]


def test_crawler_does_not_extract_links_from_non_html():
    client = FakeHttpClient(
        {
            "https://example.com/": FetchResult(
                url="https://example.com/",
                final_url="https://example.com/",
                status_code=200,
                content_type="application/pdf",
                text='<a href="/hidden">Hidden</a>',
            )
        }
    )

    result = crawl_site("https://example.com", http_client=client)

    assert client.requested_urls == ["https://example.com/"]
    assert result.pages[0].links_found == 0
    assert result.discovered_urls == []
