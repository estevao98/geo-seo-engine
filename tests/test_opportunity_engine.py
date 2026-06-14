from geo_seo_engine.opportunities import run_opportunity_engine


def test_opportunity_engine_scores_and_orders_findings_with_analytics_context():
    result = run_opportunity_engine(
        {
            "technical": {
                "findings": [
                    {
                        "id": "technical.status_not_200",
                        "title": "Status is not 200",
                        "severity": "high",
                        "category": "crawlability",
                        "page_url": "https://example.com/a",
                        "impact": "high",
                        "effort": "low",
                        "confidence": 0.9,
                        "evidence": [{"source": "inventory", "observed": 404, "expected": 200}],
                        "risk": "Important page may not be crawlable.",
                        "next_action": "Fix the response status.",
                    }
                ]
            },
            "content_quality": {
                "findings": [
                    {
                        "id": "content.thin",
                        "title": "Thin content",
                        "severity": "medium",
                        "category": "content",
                        "page_url": "https://example.com/b",
                        "confidence": 0.5,
                        "next_action": "Improve the page evidence and usefulness.",
                    }
                ]
            },
            "search_console": {
                "groups": {
                    "by_page": [
                        {
                            "key": "https://example.com/a",
                            "clicks": 10,
                            "impressions": 1000,
                            "ctr": 0.01,
                            "position": 11.2,
                        }
                    ]
                }
            },
        }
    )

    assert [opportunity.finding_id for opportunity in result.opportunities] == [
        "technical.status_not_200",
        "content.thin",
    ]
    top = result.opportunities[0]
    assert top.priority == "critical"
    assert top.score_components.analytics == 12
    assert top.analytics is not None
    assert top.evidence[0].observed == 404
    assert "Search Console summary is used only as observed demand/context" in top.rationale[-1]
    assert result.summary.inputs_present == ["technical", "content_quality", "search_console"]


def test_opportunity_engine_groups_by_page_type_and_priority():
    result = run_opportunity_engine(
        {
            "entity_readiness": {
                "findings": [
                    {
                        "id": "entity.missing_primary_entity",
                        "title": "Missing primary entity",
                        "severity": "high",
                        "category": "entity",
                        "page_url": "https://example.com/a",
                        "next_action": "Define the primary entity.",
                    }
                ]
            },
            "internal_links": {
                "findings": [
                    {
                        "id": "links.near_orphan",
                        "title": "Near orphan",
                        "severity": "medium",
                        "category": "crawlability",
                        "page_url": "https://example.com/a",
                        "next_action": "Add relevant internal links.",
                    }
                ]
            },
            "performance": {
                "findings": [
                    {
                        "id": "performance.lcp_slow",
                        "title": "Slow LCP",
                        "severity": "medium",
                        "category": "performance",
                        "page_url": "https://example.com/b",
                        "next_action": "Reduce LCP bottlenecks.",
                    }
                ]
            },
        }
    )

    assert result.summary.total_opportunities == 3
    assert result.summary.by_page["https://example.com/a"] == 2
    assert result.summary.by_type == {"crawlability": 1, "entity": 1, "performance": 1}
    assert {bucket.group_by for bucket in result.buckets_by_page} == {"page"}
    assert result.buckets_by_page[0].count == 2
    assert result.buckets_by_type[0].opportunity_ids
    assert result.buckets_by_priority


def test_opportunity_engine_handles_missing_optional_inputs():
    result = run_opportunity_engine(
        {
            "technical": {
                "findings": [
                    {
                        "id": "technical.zero_links",
                        "title": "Zero links",
                        "severity": "low",
                        "category": "technical",
                        "url": "https://example.com/",
                    }
                ]
            }
        }
    )

    opportunity = result.opportunities[0]
    assert opportunity.next_action == "Review the finding evidence and define the smallest safe remediation."
    assert opportunity.analytics is None
    assert opportunity.score_components.analytics == 0
    assert "search_console" in result.summary.inputs_missing
    assert "content_quality" in result.summary.inputs_missing
