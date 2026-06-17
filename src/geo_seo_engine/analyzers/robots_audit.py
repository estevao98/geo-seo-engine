from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx


@dataclass
class RobotsAuditResult:
    url: str
    final_url: str
    status_code: int
    content_type: str | None
    line_count: int
    user_agents: list[str]
    allow_count: int
    disallow_count: int
    sitemap_urls: list[str]
    crawl_delay_count: int
    unknown_directives: list[str]
    blocks_all: bool
    issues: list[str]


KNOWN_DIRECTIVES = {
    "user-agent",
    "allow",
    "disallow",
    "sitemap",
    "crawl-delay",
    "host",
}


def _normalize_robots_url(url: str) -> str:
    parsed = urlparse(url)

    if parsed.path.endswith("/robots.txt"):
        return url

    if not parsed.scheme or not parsed.netloc:
        return url

    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def audit_robots(url: str, timeout: float = 15.0) -> RobotsAuditResult:
    robots_url = _normalize_robots_url(url)
    issues: list[str] = []

    try:
        response = httpx.get(
            robots_url,
            follow_redirects=True,
            timeout=timeout,
            headers={
                "User-Agent": "geo-seo-engine/1.0.0 (+https://example.com)"
            },
        )
    except httpx.HTTPError as exc:
        return RobotsAuditResult(
            url=robots_url,
            final_url=robots_url,
            status_code=0,
            content_type=None,
            line_count=0,
            user_agents=[],
            allow_count=0,
            disallow_count=0,
            sitemap_urls=[],
            crawl_delay_count=0,
            unknown_directives=[],
            blocks_all=False,
            issues=[f"request_error: {exc}"],
        )

    final_url = str(response.url)
    status_code = response.status_code
    content_type = response.headers.get("content-type")

    if status_code != 200:
        issues.append(f"status_code_not_200: {status_code}")

        if 400 <= status_code < 500 and status_code != 429:
            issues.append("robots_txt_4xx_assumed_no_restrictions")
        elif status_code == 429 or 500 <= status_code < 600:
            issues.append("robots_txt_unreachable_may_affect_crawling")

        return RobotsAuditResult(
            url=robots_url,
            final_url=final_url,
            status_code=status_code,
            content_type=content_type,
            line_count=0,
            user_agents=[],
            allow_count=0,
            disallow_count=0,
            sitemap_urls=[],
            crawl_delay_count=0,
            unknown_directives=[],
            blocks_all=False,
            issues=issues,
        )

    text = response.text or ""
    lines = text.splitlines()

    user_agents: list[str] = []
    sitemap_urls: list[str] = []
    unknown_directives: list[str] = []

    allow_count = 0
    disallow_count = 0
    crawl_delay_count = 0
    blocks_all = False

    for raw_line in lines:
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if "#" in line:
            line = line.split("#", 1)[0].strip()

        if ":" not in line:
            unknown_directives.append(raw_line.strip())
            continue

        key, value = line.split(":", 1)
        key_normalized = key.strip().lower()
        value = value.strip()

        if key_normalized not in KNOWN_DIRECTIVES:
            unknown_directives.append(key.strip())
            continue

        if key_normalized == "user-agent":
            if value:
                user_agents.append(value)

        elif key_normalized == "allow":
            allow_count += 1

        elif key_normalized == "disallow":
            disallow_count += 1
            if value == "/":
                blocks_all = True

        elif key_normalized == "sitemap":
            if value:
                sitemap_urls.append(value)

        elif key_normalized == "crawl-delay":
            crawl_delay_count += 1

    if not text.strip():
        issues.append("empty_robots_txt")

    if not user_agents and status_code == 200:
        issues.append("missing_user_agent")

    if blocks_all:
        issues.append("disallow_all_found")

    if not sitemap_urls:
        issues.append("missing_sitemap_directive")

    if unknown_directives:
        issues.append("unknown_or_invalid_directives_found")

    return RobotsAuditResult(
        url=robots_url,
        final_url=final_url,
        status_code=status_code,
        content_type=content_type,
        line_count=len(lines),
        user_agents=sorted(set(user_agents)),
        allow_count=allow_count,
        disallow_count=disallow_count,
        sitemap_urls=sitemap_urls,
        crawl_delay_count=crawl_delay_count,
        unknown_directives=unknown_directives,
        blocks_all=blocks_all,
        issues=issues,
    )
