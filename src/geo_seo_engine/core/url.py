from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field


SUPPORTED_URL_SCHEMES = {"http", "https"}
DEFAULT_TRACKING_PARAMS = (
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
)


class UrlNormalizationOptions(BaseModel):
    model_config = ConfigDict(frozen=True)

    remove_fragment: bool = True
    lowercase_scheme_host: bool = True
    remove_default_port: bool = True
    normalize_empty_path_to_slash: bool = True
    strip_trailing_slash: bool = False
    sort_query_params: bool = False
    remove_tracking_params: bool = False
    tracking_params: list[str] = Field(default_factory=lambda: list(DEFAULT_TRACKING_PARAMS))


class UrlNormalizationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    raw_url: str
    normalized_url: str
    base_url: str | None = None
    host: str
    path: str
    query: str
    removed_fragment: str | None = None


def normalize_url(
    raw_url: str,
    base_url: str | None = None,
    options: UrlNormalizationOptions | None = None,
) -> UrlNormalizationResult:
    """Normalize an HTTP(S) URL without performing network requests."""
    active_options = options or UrlNormalizationOptions()
    raw_value = _clean_url_value(raw_url, "raw_url")
    base_value = None

    if base_url is not None:
        base_value = _clean_url_value(base_url, "base_url")
        base_parts = _parse_url(base_value, "base_url")
        _validate_http_url_parts(base_parts, base_value, "base_url")
        resolved_url = urljoin(base_value, raw_value)
    else:
        resolved_url = raw_value

    parts = _parse_url(resolved_url, "URL")
    _validate_http_url_parts(parts, resolved_url, "URL")

    scheme = parts.scheme.lower() if active_options.lowercase_scheme_host else parts.scheme
    host, netloc = _normalized_host_and_netloc(parts, scheme, active_options)
    path = _normalized_path(parts.path, active_options)
    query = _normalized_query(parts.query, active_options)
    fragment = "" if active_options.remove_fragment else parts.fragment
    removed_fragment = parts.fragment if active_options.remove_fragment and parts.fragment else None
    normalized_url = urlunsplit((scheme, netloc, path, query, fragment))

    return UrlNormalizationResult(
        raw_url=raw_url,
        normalized_url=normalized_url,
        base_url=base_url,
        host=host,
        path=path,
        query=query,
        removed_fragment=removed_fragment,
    )


def is_same_site(url: str, allowed_hosts: list[str]) -> bool:
    host = url_host(url)
    if host is None:
        return False
    normalized_allowed_hosts = {allowed_host.strip().lower() for allowed_host in allowed_hosts}
    return host.lower() in normalized_allowed_hosts


def url_host(url: str) -> str | None:
    try:
        value = _clean_url_value(url, "url")
        parts = _parse_url(value, "url")
    except ValueError:
        return None
    return parts.hostname.lower() if parts.hostname else None


def resolve_url(raw_url: str, base_url: str) -> str:
    raw_value = _clean_url_value(raw_url, "raw_url")
    base_value = _clean_url_value(base_url, "base_url")
    base_parts = _parse_url(base_value, "base_url")
    _validate_http_url_parts(base_parts, base_value, "base_url")
    return urljoin(base_value, raw_value)


def _clean_url_value(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    if any(character.isspace() for character in cleaned):
        raise ValueError(f"{field_name} cannot contain whitespace")
    return cleaned


def _parse_url(value: str, field_name: str):
    try:
        parts = urlsplit(value)
        _ = parts.port
    except ValueError as error:
        raise ValueError(f"{field_name} is not a valid URL: {value}") from error
    return parts


def _validate_http_url_parts(parts, value: str, field_name: str) -> None:
    scheme = parts.scheme.lower()
    if scheme not in SUPPORTED_URL_SCHEMES:
        raise ValueError(f"{field_name} must use http or https scheme: {value}")
    if not parts.netloc or not parts.hostname:
        raise ValueError(f"{field_name} must be an absolute URL with a host: {value}")
    if any(character.isspace() for character in parts.hostname):
        raise ValueError(f"{field_name} host cannot contain whitespace: {value}")


def _normalized_host_and_netloc(parts, scheme: str, options: UrlNormalizationOptions) -> tuple[str, str]:
    userinfo, host, is_bracketed_ipv6 = _split_netloc_host(parts.netloc)
    if not host:
        raise ValueError(f"URL must be an absolute URL with a host: {parts.geturl()}")

    normalized_host = host.lower() if options.lowercase_scheme_host else host
    port = parts.port
    if options.remove_default_port and (
        (scheme.lower() == "http" and port == 80) or (scheme.lower() == "https" and port == 443)
    ):
        port = None

    netloc_host = f"[{normalized_host}]" if is_bracketed_ipv6 else normalized_host
    netloc = f"{userinfo}{netloc_host}"
    if port is not None:
        netloc = f"{netloc}:{port}"
    return normalized_host, netloc


def _split_netloc_host(netloc: str) -> tuple[str, str, bool]:
    userinfo = ""
    host_port = netloc
    if "@" in host_port:
        userinfo, host_port = host_port.rsplit("@", 1)
        userinfo = f"{userinfo}@"

    if host_port.startswith("["):
        host_end = host_port.find("]")
        if host_end == -1:
            raise ValueError(f"URL is not a valid URL: {netloc}")
        host = host_port[1:host_end]
        remainder = host_port[host_end + 1 :]
        if remainder and not remainder.startswith(":"):
            raise ValueError(f"URL is not a valid URL: {netloc}")
        if remainder == ":":
            raise ValueError(f"URL is not a valid URL: {netloc}")
        return userinfo, host, True

    host = host_port
    if ":" in host_port:
        host, _, port = host_port.rpartition(":")
        if not port:
            raise ValueError(f"URL is not a valid URL: {netloc}")
    return userinfo, host, False


def _normalized_path(path: str, options: UrlNormalizationOptions) -> str:
    normalized_path = path
    if options.normalize_empty_path_to_slash and not normalized_path:
        normalized_path = "/"
    if options.strip_trailing_slash and normalized_path != "/":
        normalized_path = normalized_path.rstrip("/") or "/"
    return normalized_path


def _normalized_query(query: str, options: UrlNormalizationOptions) -> str:
    if not query or not (options.remove_tracking_params or options.sort_query_params):
        return query

    params = parse_qsl(query, keep_blank_values=True)
    if options.remove_tracking_params:
        tracking_params = {param.lower() for param in options.tracking_params}
        params = [(key, value) for key, value in params if key.lower() not in tracking_params]
    if options.sort_query_params:
        params = sorted(params)
    return urlencode(params, doseq=True)
