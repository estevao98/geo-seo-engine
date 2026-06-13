import httpx

from geo_seo_engine.http import HttpClient, HttpClientConfig


def test_fetch_200_returns_status_text_final_url_and_content_type():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            text="hello",
            headers={"content-type": "text/html; charset=utf-8"},
            request=request,
        )
    )
    client = HttpClient(HttpClientConfig(retries=0), transport=transport)

    result = client.fetch("https://example.com/page")

    assert result.ok is True
    assert result.status_code == 200
    assert result.text == "hello"
    assert result.final_url == "https://example.com/page"
    assert result.content_type == "text/html; charset=utf-8"


def test_fetch_404_returns_status_without_unhandled_exception():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(404, text="not found", request=request)
    )
    client = HttpClient(HttpClientConfig(retries=0), transport=transport)

    result = client.fetch("https://example.com/missing")

    assert result.ok is False
    assert result.status_code == 404
    assert result.error is None
    assert result.text == "not found"


def test_timeout_returns_structured_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    client = HttpClient(
        HttpClientConfig(retries=0),
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch("https://example.com/slow")

    assert result.status_code == 0
    assert result.error == "timeout: timed out"


def test_connection_error_returns_structured_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    client = HttpClient(
        HttpClientConfig(retries=0),
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch("https://example.com/down")

    assert result.status_code == 0
    assert result.error == "request_error: connection failed"


def test_custom_user_agent_is_sent():
    seen_user_agent = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_user_agent
        seen_user_agent = request.headers["user-agent"]
        return httpx.Response(200, text="ok", request=request)

    client = HttpClient(
        HttpClientConfig(user_agent="custom-agent", retries=0),
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch("https://example.com")

    assert result.status_code == 200
    assert seen_user_agent == "custom-agent"


def test_follow_redirects_is_respected_when_enabled():
    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == "https://example.com/old":
            return httpx.Response(
                302,
                headers={"location": "https://example.com/new"},
                request=request,
            )
        return httpx.Response(200, text="new", request=request)

    client = HttpClient(
        HttpClientConfig(follow_redirects=True, retries=0),
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch("https://example.com/old")

    assert result.status_code == 200
    assert result.final_url == "https://example.com/new"
    assert result.redirect_chain == ["https://example.com/old"]


def test_follow_redirects_is_respected_when_disabled():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            302,
            headers={"location": "https://example.com/new"},
            request=request,
        )
    )
    client = HttpClient(
        HttpClientConfig(follow_redirects=False, retries=0),
        transport=transport,
    )

    result = client.fetch("https://example.com/old")

    assert result.status_code == 302
    assert result.final_url == "https://example.com/old"
    assert result.redirect_chain == []


def test_max_response_bytes_limits_response_text():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"abcdef", request=request)
    )
    client = HttpClient(
        HttpClientConfig(max_response_bytes=3, retries=0),
        transport=transport,
    )

    result = client.fetch("https://example.com/large")

    assert result.text == "abc"


def test_private_host_is_blocked_when_policy_is_active():
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, text="ok", request=request)

    client = HttpClient(
        HttpClientConfig(block_private_hosts=True, retries=0),
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch("http://127.0.0.1/private")

    assert result.status_code == 0
    assert result.error == "blocked_private_host: 127.0.0.1"
    assert called is False


def test_metadata_link_local_host_is_blocked_when_policy_is_active():
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, text="ok", request=request)

    client = HttpClient(
        HttpClientConfig(block_private_hosts=True, retries=0),
        transport=httpx.MockTransport(handler),
    )

    result = client.fetch("http://169.254.169.254/")

    assert result.status_code == 0
    assert result.error == "blocked_private_host: 169.254.169.254"
    assert called is False


def test_private_host_is_not_blocked_when_policy_is_disabled():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text="local ok", request=request)
    )
    client = HttpClient(
        HttpClientConfig(block_private_hosts=False, retries=0),
        transport=transport,
    )

    result = client.fetch("http://127.0.0.1/private")

    assert result.status_code == 200
    assert result.text == "local ok"
