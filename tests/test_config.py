import pytest

from geo_seo_engine.config import ProjectConfig, load_project_config, validate_project_config


def test_minimal_config_valid(tmp_path):
    config_path = tmp_path / "geo-seo.yml"
    config_path.write_text(
        "project_name: Minimal\nbase_url: https://example.com\n",
        encoding="utf-8",
    )

    config = validate_project_config(config_path)

    assert config.project_name == "Minimal"
    assert config.base_url == "https://example.com"
    assert config.allowed_hosts == ["example.com"]
    assert config.start_urls == ["https://example.com"]
    assert config.output_dir.name == "reports"
    assert config.http.follow_redirects is True
    assert config.crawler.max_pages == 100
    assert config.privacy.collect_personal_data is False


def test_complete_config_valid(tmp_path):
    config_path = tmp_path / "geo-seo.yml"
    config_path.write_text(
        """
project_name: Complete
base_url: https://example.com
allowed_hosts:
  - example.com
start_urls:
  - https://example.com
sitemap_urls:
  - https://example.com/sitemap.xml
include_patterns:
  - "/*"
exclude_patterns:
  - "/admin/*"
output_dir: custom-reports
http:
  timeout_seconds: 5
  follow_redirects: true
  user_agent: custom-agent
  retries: 2
crawler:
  max_pages: 25
  max_depth: 3
  crawl_delay_seconds: 0.5
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
""".lstrip(),
        encoding="utf-8",
    )

    config = load_project_config(config_path)

    assert config.project_name == "Complete"
    assert config.output_dir.name == "custom-reports"
    assert config.http.timeout_seconds == 5
    assert config.http.user_agent == "custom-agent"
    assert config.crawler.max_pages == 25
    assert config.integrations.pagespeed_insights is False


def test_invalid_config_fails_with_clear_error(tmp_path):
    config_path = tmp_path / "geo-seo.yml"
    config_path.write_text(
        "project_name: Invalid\nbase_url: not-a-url\nunknown: value\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as error:
        validate_project_config(config_path)

    message = str(error.value)
    assert "Invalid project config" in message
    assert "base_url" in message
    assert "unknown" in message


def test_load_project_config_returns_project_config(tmp_path):
    config_path = tmp_path / "geo-seo.yml"
    config_path.write_text(
        "project_name: Loader\nbase_url: https://example.com\n",
        encoding="utf-8",
    )

    assert isinstance(load_project_config(config_path), ProjectConfig)


def test_rejects_start_url_outside_allowed_hosts(tmp_path):
    config_path = tmp_path / "geo-seo.yml"
    config_path.write_text(
        """
project_name: Host Guard
base_url: https://example.com
allowed_hosts:
  - example.com
start_urls:
  - https://other.example/path
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as error:
        load_project_config(config_path)

    assert "outside allowed_hosts" in str(error.value)
