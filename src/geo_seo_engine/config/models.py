from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


DEFAULT_USER_AGENT = "geo-seo-engine/1.0.0 (+https://example.com)"


class ConfigBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _validate_http_url(value: str, field_name: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field_name} must be an absolute http or https URL")
    return value


def _url_host(value: str) -> str:
    parsed = urlparse(value)
    return (parsed.hostname or "").lower()


class HttpConfig(ConfigBaseModel):
    timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    follow_redirects: bool = True
    user_agent: str = Field(default=DEFAULT_USER_AGENT, min_length=1, max_length=300)
    retries: int = Field(default=1, ge=0, le=5)
    max_response_bytes: int = Field(default=2_000_000, ge=1, le=20_000_000)
    block_private_hosts: bool = False


class CrawlerConfig(ConfigBaseModel):
    max_pages: int = Field(default=100, ge=1, le=10_000)
    max_depth: int = Field(default=2, ge=0, le=20)
    crawl_delay_seconds: float = Field(default=1.0, ge=0, le=60)
    respect_robots_txt: bool = True


class PrivacyConfig(ConfigBaseModel):
    store_raw_html: bool = False
    store_response_headers: bool = False
    redact_query_params: bool = True
    collect_personal_data: bool = False


class IntegrationConfig(ConfigBaseModel):
    google_search_console: bool = False
    google_analytics: bool = False
    pagespeed_insights: bool = False


class ProjectConfig(ConfigBaseModel):
    project_name: str = Field(min_length=1, max_length=120)
    base_url: str
    allowed_hosts: list[str] = Field(default_factory=list)
    start_urls: list[str] = Field(default_factory=list)
    sitemap_urls: list[str] = Field(default_factory=list)
    include_patterns: list[str] = Field(default_factory=lambda: ["*"])
    exclude_patterns: list[str] = Field(default_factory=list)
    output_dir: Path = Path("reports")
    http: HttpConfig = Field(default_factory=HttpConfig)
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    integrations: IntegrationConfig = Field(default_factory=IntegrationConfig)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        return _validate_http_url(value, "base_url")

    @field_validator("allowed_hosts")
    @classmethod
    def validate_allowed_hosts(cls, value: list[str]) -> list[str]:
        hosts: list[str] = []
        for host in value:
            if not host:
                raise ValueError("allowed_hosts cannot contain empty values")
            if "://" in host or "/" in host:
                raise ValueError("allowed_hosts entries must be hostnames, not URLs")
            hosts.append(host.lower())
        return hosts

    @field_validator("start_urls", "sitemap_urls")
    @classmethod
    def validate_url_list(cls, value: list[str], info: Any) -> list[str]:
        field_name = info.field_name or "url list"
        return [_validate_http_url(url, field_name) for url in value]

    @field_validator("include_patterns", "exclude_patterns")
    @classmethod
    def validate_patterns(cls, value: list[str], info: Any) -> list[str]:
        field_name = info.field_name or "patterns"
        if any(not pattern for pattern in value):
            raise ValueError(f"{field_name} cannot contain empty patterns")
        return value

    @model_validator(mode="after")
    def fill_and_validate_hosts(self) -> ProjectConfig:
        base_host = _url_host(self.base_url)
        if not base_host:
            raise ValueError("base_url must include a hostname")

        if not self.allowed_hosts:
            self.allowed_hosts = [base_host]

        if not self.start_urls:
            self.start_urls = [self.base_url]

        allowed = set(self.allowed_hosts)
        for field_name in ("start_urls", "sitemap_urls"):
            for url in getattr(self, field_name):
                host = _url_host(url)
                if host not in allowed:
                    raise ValueError(f"{field_name} contains URL outside allowed_hosts: {url}")

        return self
