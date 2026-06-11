from __future__ import annotations

import ipaddress
import time
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import httpx

from geo_seo_engine.config.models import HttpConfig


HttpClientConfig = HttpConfig

_PRIVATE_IP_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in (
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    )
)


@dataclass(frozen=True)
class FetchRequest:
    url: str
    timeout_seconds: float | None = None
    follow_redirects: bool | None = None
    user_agent: str | None = None
    max_response_bytes: int | None = None
    block_private_hosts: bool | None = None


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    text: str = ""
    content_type: str = ""
    elapsed_ms: int | None = None
    error: str | None = None
    redirect_chain: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.error is None and 200 <= self.status_code < 400


class HttpClient:
    def __init__(
        self,
        config: HttpClientConfig | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config or HttpClientConfig()
        self._transport = transport

    def fetch(self, request: str | FetchRequest) -> FetchResult:
        if isinstance(request, FetchRequest):
            fetch_request = request
        else:
            fetch_request = FetchRequest(url=request)
        config = _apply_request_overrides(self.config, fetch_request)

        blocked_error = _private_host_error(fetch_request.url, config.block_private_hosts)
        if blocked_error is not None:
            return _error_result(fetch_request.url, blocked_error)

        headers = {"User-Agent": config.user_agent}
        last_error: str | None = None

        for _ in range(config.retries + 1):
            started = time.perf_counter()
            try:
                with httpx.Client(
                    timeout=config.timeout_seconds,
                    transport=self._transport,
                ) as client:
                    with client.stream(
                        "GET",
                        fetch_request.url,
                        follow_redirects=config.follow_redirects,
                        headers=headers,
                    ) as response:
                        body = _read_limited_body(response, config.max_response_bytes)
                        elapsed_ms = int((time.perf_counter() - started) * 1000)
                        response_headers = dict(response.headers)
                        content_type = response_headers.get("content-type", "")
                        return FetchResult(
                            url=fetch_request.url,
                            final_url=str(response.url),
                            status_code=response.status_code,
                            headers=response_headers,
                            text=_decode_body(body, response.encoding),
                            content_type=content_type,
                            elapsed_ms=elapsed_ms,
                            redirect_chain=[str(item.url) for item in response.history],
                        )
            except httpx.TimeoutException as exc:
                last_error = _format_error("timeout", exc)
            except httpx.HTTPError as exc:
                last_error = _format_error("request_error", exc)
            except ValueError as exc:
                last_error = _format_error("invalid_request", exc)
                break

        return _error_result(fetch_request.url, last_error or "request_error")


def fetch_url(url: str, config: HttpClientConfig | None = None) -> FetchResult:
    return HttpClient(config=config).fetch(url)


def _apply_request_overrides(
    config: HttpClientConfig,
    request: FetchRequest,
) -> HttpClientConfig:
    updates = {
        field_name: value
        for field_name, value in {
            "timeout_seconds": request.timeout_seconds,
            "follow_redirects": request.follow_redirects,
            "user_agent": request.user_agent,
            "max_response_bytes": request.max_response_bytes,
            "block_private_hosts": request.block_private_hosts,
        }.items()
        if value is not None
    }
    return config.model_copy(update=updates)


def _private_host_error(url: str, block_private_hosts: bool) -> str | None:
    if not block_private_hosts:
        return None

    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        return f"invalid_url: {exc}"

    hostname = (parsed.hostname or "").strip().lower()
    if not hostname:
        return "invalid_url: missing hostname"
    if parsed.scheme.lower() not in {"http", "https"}:
        return f"invalid_url: unsupported scheme {parsed.scheme}"

    if hostname == "localhost":
        return "blocked_private_host: localhost"

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return None

    if any(address in network for network in _PRIVATE_IP_NETWORKS):
        return f"blocked_private_host: {hostname}"
    return None


def _read_limited_body(response: httpx.Response, max_response_bytes: int) -> bytes:
    chunks: list[bytes] = []
    bytes_read = 0

    for chunk in response.iter_bytes():
        remaining = max_response_bytes - bytes_read
        if remaining <= 0:
            break
        if len(chunk) > remaining:
            chunks.append(chunk[:remaining])
            break
        chunks.append(chunk)
        bytes_read += len(chunk)

    return b"".join(chunks)


def _decode_body(body: bytes, encoding: str | None) -> str:
    return body.decode(encoding or "utf-8", errors="replace")


def _format_error(prefix: str, exc: Exception) -> str:
    message = str(exc).strip()
    return f"{prefix}: {message}" if message else prefix


def _error_result(url: str, error: str) -> FetchResult:
    return FetchResult(
        url=url,
        final_url=url,
        status_code=0,
        headers={},
        text="",
        content_type="",
        error=error,
    )
