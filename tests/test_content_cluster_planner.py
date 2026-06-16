import json

from geo_seo_engine.content_clusters import plan_content_clusters


def test_content_cluster_planner_groups_deterministically_from_local_inputs():
    payload = _payload()

    first = plan_content_clusters(payload)
    second = plan_content_clusters(payload)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.summary.total_clusters == 1
    cluster = first.clusters[0]
    assert cluster.id == "content_cluster.entity-seo"
    assert cluster.label == "Entity SEO"
    assert cluster.pillar_page_url == "https://example.com/guides/entity-seo"
    assert cluster.supporting_page_urls == ["https://example.com/blog/entity-seo-checklist"]
    assert cluster.entities == ["Entity SEO"]
    assert "schema" in cluster.topics
    assert cluster.source_brief_ids == ["content_brief.entity_seo"]
    assert cluster.source_opportunity_ids == ["opportunity.1"]
    assert cluster.source_finding_ids == ["entity.missing_primary_entity"]


def test_content_cluster_planner_handles_missing_optional_inputs():
    result = plan_content_clusters(
        {
            "main_content": {
                "pages": [
                    {
                        "page_url": "https://example.com/a",
                        "title": "Example guide",
                        "headings": [{"level": 1, "text": "Example guide"}],
                    }
                ]
            }
        }
    )

    assert result.summary.total_clusters == 1
    assert result.clusters[0].pillar_page_url == "https://example.com/a"
    assert result.clusters[0].internal_link_recommendations == []
    assert result.summary.total_briefs == 0
    assert "briefs" in result.summary.inputs_missing
    assert "search_console" in result.summary.inputs_missing
    assert any("No structured evidence" in limitation for limitation in result.clusters[0].limitations)


def test_content_cluster_planner_preserves_source_ids_and_evidence():
    result = plan_content_clusters(_payload())

    cluster = result.clusters[0]
    assert {ref.source_id for ref in cluster.source_refs} >= {
        "page.entity_guide",
        "page.entity_checklist",
        "content_brief.entity_seo",
        "opportunity.1",
    }
    assert cluster.evidence[0].source == "entity_readiness"
    assert cluster.evidence[0].observed == "No primary entity"
    assert cluster.source_page_ids == ["page.entity_guide", "page.entity_checklist"]


def test_content_cluster_planner_recommends_missing_internal_links_only_within_cluster():
    result = plan_content_clusters(_payload())

    recommendations = result.clusters[0].internal_link_recommendations

    assert [(item.source_url, item.target_url) for item in recommendations] == [
        ("https://example.com/guides/entity-seo", "https://example.com/blog/entity-seo-checklist")
    ]
    assert recommendations[0].anchor_text == "entity seo checklist"
    assert "opportunity.1" in recommendations[0].source_ids


def test_content_cluster_planner_json_serialization_is_stable():
    result = plan_content_clusters(_payload())

    rendered = json.dumps(result.model_dump(mode="json"), sort_keys=True)
    data = json.loads(rendered)

    assert data["summary"]["by_priority"] == {"critical": 1}
    assert data["summary"]["by_type"]["risk_remediation"] == 1
    assert data["clusters"][0]["confidence"] == 1.0


def _payload():
    return {
        "main_content": {
            "pages": [
                {
                    "id": "page.entity_guide",
                    "page_url": "https://example.com/guides/entity-seo",
                    "title": "Entity SEO guide",
                    "headings": [{"level": 1, "text": "Entity SEO"}],
                    "word_count": 900,
                },
                {
                    "id": "page.entity_checklist",
                    "page_url": "https://example.com/blog/entity-seo-checklist",
                    "title": "Entity SEO checklist",
                    "headings": [{"level": 1, "text": "Entity SEO checklist"}],
                    "word_count": 500,
                },
            ]
        },
        "entity_readiness": {
            "page_audits": [
                {
                    "page_url": "https://example.com/guides/entity-seo",
                    "primary_entity": "Entity SEO",
                    "topic_terms": ["entities", "schema"],
                },
                {
                    "page_url": "https://example.com/blog/entity-seo-checklist",
                    "primary_entity": "Entity SEO",
                    "topic_terms": ["entities", "checklist"],
                },
            ]
        },
        "opportunities": [
            {
                "id": "opportunity.1",
                "finding_id": "entity.missing_primary_entity",
                "source": "entity_readiness",
                "type": "entity",
                "page_url": "https://example.com/guides/entity-seo",
                "title": "Missing primary entity",
                "priority": "critical",
                "evidence": [
                    {
                        "source": "entity_readiness",
                        "observed": "No primary entity",
                        "expected": "Primary entity",
                    }
                ],
            }
        ],
        "content_briefs": {
            "briefs": [
                {
                    "id": "content_brief.entity_seo",
                    "target_url": "https://example.com/guides/entity-seo",
                    "brief_type": "risk_remediation",
                    "priority": "critical",
                    "primary_topic_entity_cue": "Entity SEO",
                    "content_gaps": ["Primary entity missing"],
                    "evidence": [
                        {
                            "source": "entity_readiness",
                            "observed": "No primary entity",
                            "expected": "Primary entity",
                        }
                    ],
                }
            ]
        },
        "internal_links": {
            "edges": [
                {
                    "source_url": "https://example.com/blog/entity-seo-checklist",
                    "target_url": "https://example.com/guides/entity-seo",
                    "anchor_text": "Entity SEO guide",
                }
            ]
        },
        "search_console": {
            "rows": [
                {
                    "query": "what is entity seo",
                    "page": "https://example.com/guides/entity-seo",
                    "normalized_page": "https://example.com/guides/entity-seo",
                    "impressions": 200,
                }
            ]
        },
    }
