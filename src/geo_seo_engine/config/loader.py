from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from geo_seo_engine.config.models import ProjectConfig


DEFAULT_PROJECT_CONFIG_YAML = """# Safe starter config for geo-seo-engine.
# Do not put tokens, passwords, API keys or private customer data in this file.
project_name: Example Project
base_url: https://example.com
allowed_hosts:
  - example.com
start_urls:
  - https://example.com
sitemap_urls:
  - https://example.com/sitemap.xml
include_patterns:
  - "*"
exclude_patterns:
  - "/admin/*"
  - "/private/*"
output_dir: reports
http:
  timeout_seconds: 10
  follow_redirects: true
  user_agent: geo-seo-engine/0.1.0 (+https://example.com)
  retries: 1
  max_response_bytes: 2000000
  block_private_hosts: false
crawler:
  max_pages: 100
  max_depth: 2
  crawl_delay_seconds: 1
  respect_robots_txt: true
privacy:
  store_raw_html: false
  store_response_headers: false
  redact_query_params: true
  collect_personal_data: false
integrations:
  google_search_console: false
  google_analytics: false
  pagespeed_insights: false
"""


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Could not read config file {path}: {exc}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in config file {path}: {exc}") from exc

    if data is None:
        raise ValueError(f"Config file {path} is empty")
    if not isinstance(data, dict):
        raise ValueError(f"Config file {path} must contain a YAML mapping")

    return data


def load_project_config(path: str | Path) -> ProjectConfig:
    config_path = Path(path)
    data = _read_yaml_mapping(config_path)
    try:
        return ProjectConfig.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid project config {config_path}: {exc}") from exc


def validate_project_config(path: str | Path) -> ProjectConfig:
    return load_project_config(path)
