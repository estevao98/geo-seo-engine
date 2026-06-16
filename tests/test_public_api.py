from geo_seo_engine.ai_readiness import run_ai_readiness_simulation
from geo_seo_engine.config import ProjectConfig
from geo_seo_engine.content_clusters import plan_content_clusters
from geo_seo_engine.core import (
    Evidence,
    IssueCategory,
    Severity,
    is_same_site,
    normalize_url,
    resolve_url,
)
from geo_seo_engine.crawler import CrawlOptions, crawl_site
from geo_seo_engine.http import FetchResult, HttpClient
from geo_seo_engine.inventory import build_url_inventory
from geo_seo_engine.opportunities import run_opportunity_engine
from geo_seo_engine.technical import TechnicalAuditOptions, run_technical_audit


def test_foundation_public_api_imports_are_available():
    assert Severity.HIGH == "high"
    assert IssueCategory.CRAWLABILITY == "crawlability"
    assert Evidence(source="test", observed="ok").source == "test"

    normalized = normalize_url("HTTPS://Example.com/path#section")
    assert normalized.normalized_url == "https://example.com/path"
    assert resolve_url("/docs", "https://example.com/base/") == "https://example.com/docs"
    assert is_same_site("https://example.com/docs", ["example.com"]) is True

    config = ProjectConfig(project_name="Example", base_url="https://example.com")
    assert config.allowed_hosts == ["example.com"]
    assert config.start_urls == ["https://example.com"]

    assert isinstance(HttpClient(), HttpClient)
    assert FetchResult(
        url="https://example.com/",
        final_url="https://example.com/",
        status_code=200,
    ).ok is True
    assert CrawlOptions(max_pages=1).max_pages == 1
    assert callable(crawl_site)
    assert callable(build_url_inventory)
    assert callable(run_technical_audit)
    assert callable(run_opportunity_engine)
    assert callable(plan_content_clusters)
    assert callable(run_ai_readiness_simulation)
    assert TechnicalAuditOptions(max_depth_warning=1).max_depth_warning == 1
