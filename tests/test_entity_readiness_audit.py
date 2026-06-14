import json

from geo_seo_engine.content import extract_main_content_from_html
from geo_seo_engine.entity_readiness import run_entity_readiness_audit


def test_entity_readiness_positive_signals_pass_without_major_gaps():
    html = """
    <html>
      <head>
        <title>Entity SEO Guide for SaaS Teams</title>
        <meta name="description" content="Entity SEO guide for SaaS teams with author and publisher context.">
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@graph": [
            {"@type": "Organization", "name": "Acme Software", "sameAs": ["https://www.linkedin.com/company/acme"]},
            {"@type": "Person", "name": "Ana Silva", "sameAs": "https://example.com/ana"},
            {"@type": "Article", "headline": "Entity SEO Guide for SaaS Teams", "author": {"@type": "Person", "name": "Ana Silva"}, "publisher": {"@type": "Organization", "name": "Acme Software"}},
            {"@type": "WebPage", "name": "Entity SEO Guide for SaaS Teams"},
            {"@type": "BreadcrumbList", "name": "Guides"}
          ]
        }
        </script>
      </head>
      <body>
        <main>
          <p class="byline">Written by Ana Silva</p>
          <p class="publisher">Published by Acme Software</p>
          <h1>Entity SEO Guide for SaaS Teams</h1>
          <p>Entity SEO helps SaaS teams clarify products, authors, publishers and topics for search systems.</p>
          <p>This entity guide explains topic consistency, organization context, author context and structured data.</p>
          <p>Teams can use entity signals to make content easier to understand without artificial ranking promises.</p>
        </main>
      </body>
    </html>
    """
    page = extract_main_content_from_html(html, "https://example.com/entity-guide")

    result = run_entity_readiness_audit([page], html_by_url={page.page_url: html})

    assert result.summary.total_pages == 1
    assert result.summary.pages_with_primary_entity == 1
    assert result.summary.pages_with_author_signal == 1
    assert result.summary.pages_with_publisher_signal == 1
    assert result.summary.pages_with_same_as_signal == 1
    assert result.summary.pages_with_article_schema == 1
    assert result.summary.pages_with_web_page_schema == 1
    assert result.summary.pages_with_breadcrumb_schema == 1
    assert "entity.missing_author_signal" not in _finding_ids(result)
    assert "entity.weak_publisher_signal" not in _finding_ids(result)
    assert "entity.metadata_inconsistency" not in _finding_ids(result)


def test_entity_readiness_reports_partial_author_and_same_as_gaps():
    html = """
    <html>
      <head>
        <title>Technical SEO Migration Checklist</title>
        <meta name="description" content="Technical SEO migration checklist for product teams.">
        <script type="application/ld+json">
        {"@context":"https://schema.org","@type":"Organization","name":"Acme Software"}
        </script>
      </head>
      <body><main><h1>Technical SEO Migration Checklist</h1>
        <p>Technical SEO migration planning keeps redirects, canonicals, content and analytics aligned.</p>
        <p>This checklist helps product teams prepare technical SEO migration steps before release.</p>
      </main></body>
    </html>
    """
    page = extract_main_content_from_html(html, "https://example.com/migration")

    result = run_entity_readiness_audit([page], html_by_url={page.page_url: html})

    assert "entity.missing_author_signal" in _finding_ids(result)
    assert "entity.missing_same_as_signal" in _finding_ids(result)
    assert "entity.weak_publisher_signal" not in _finding_ids(result)
    assert result.summary.pages_with_publisher_signal == 1


def test_entity_readiness_reports_missing_signals_and_inconsistent_metadata():
    html = """
    <html>
      <head>
        <title>Pricing Plans</title>
        <meta name="description" content="Enterprise billing automation for finance teams.">
      </head>
      <body><main><h1>Banana Recipes</h1><p>Short page.</p></main></body>
    </html>
    """
    page = extract_main_content_from_html(html, "https://example.com/confusing")

    result = run_entity_readiness_audit([page], html_by_url={page.page_url: html})

    assert "entity.missing_primary_entity" in _finding_ids(result)
    assert "entity.unclear_topic" in _finding_ids(result)
    assert "entity.missing_author_signal" in _finding_ids(result)
    assert "entity.weak_publisher_signal" in _finding_ids(result)
    assert "entity.missing_structured_data" in _finding_ids(result)
    assert "entity.metadata_inconsistency" in _finding_ids(result)


def test_entity_readiness_output_is_json_serializable():
    html = "<main><h1>Entity Guide</h1><p>Entity guide content for teams and publishers.</p></main>"
    page = extract_main_content_from_html(html, "https://example.com/entity-guide")

    result = run_entity_readiness_audit([page], html_by_url={page.page_url: html})
    rendered = json.dumps(result.model_dump(mode="json"), sort_keys=True)

    assert "entity.missing_author_signal" in rendered


def _finding_ids(result):
    return [finding.id for finding in result.findings]
