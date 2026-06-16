import json

from geo_seo_engine.senior_report import generate_senior_report


def test_senior_report_is_deterministic_and_separates_executive_from_actions():
    payload = _payload()

    first = generate_senior_report(payload)
    second = generate_senior_report(payload)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.executive_summary.top_priority == "critical"
    assert first.executive_summary.total_findings == 3
    assert first.executive_summary.total_opportunities == 1
    assert first.operational_action_queue[0].priority == "critical"
    assert first.operational_action_queue[0].action == "Fix the status code."
    assert "No traffic, ranking, revenue, ROI or AI visibility forecast is included." in first.executive_summary.statements


def test_senior_report_handles_missing_optional_inputs_with_limitations():
    result = generate_senior_report({"technical": {"findings": []}})

    assert result.executive_summary.available_inputs == ["technical"]
    assert "content_quality" in result.executive_summary.missing_inputs
    assert result.ai_geo_readiness_summary.targets == 0
    assert any("Optional input 'search_console'" in item for item in result.limitations_and_assumptions)
    assert any("does not forecast rankings" in item for item in result.limitations_and_assumptions)


def test_senior_report_preserves_evidence_and_source_ids():
    result = generate_senior_report(_payload())

    risk = result.top_risks_and_priorities[0]

    assert risk.id == "technical.status_not_200"
    assert risk.evidence[0].source == "technical"
    assert risk.evidence[0].observed == 500
    assert any(ref.source_id == "entity.missing_primary_entity" for ref in result.evidence_source_references)
    assert any("opportunity.1" in action.source_ids for action in result.operational_action_queue)


def test_senior_report_summarizes_ai_geo_and_cluster_content_planning():
    result = generate_senior_report(_payload())

    assert result.ai_geo_readiness_summary.targets == 1
    assert result.ai_geo_readiness_summary.average_score == 52.0
    assert result.ai_geo_readiness_summary.by_readiness_band == {"limited": 1}
    assert result.cluster_and_content_planning_summary.total_clusters == 1
    assert result.cluster_and_content_planning_summary.total_briefs == 1
    assert result.cluster_and_content_planning_summary.total_link_recommendations == 1
    assert result.cluster_and_content_planning_summary.cluster_ids == ["content_cluster.entity-seo"]


def test_senior_report_json_serialization_is_stable():
    result = generate_senior_report(_payload())

    rendered = json.dumps(result.model_dump(mode="json"), sort_keys=True)
    data = json.loads(rendered)

    assert data["report_type"] == "senior_executive_operational"
    assert data["opportunity_and_remediation_summary"]["by_priority"] == {"high": 1}
    assert data["health_readiness_snapshot"]["by_severity"] == {"critical": 1, "high": 1, "medium": 1}


def _payload():
    return {
        "technical": {
            "findings": [
                {
                    "id": "technical.status_not_200",
                    "title": "Status is not 200",
                    "severity": "critical",
                    "category": "crawlability",
                    "url": "https://example.com/",
                    "risk": "Search engines and users may not reach the page.",
                    "next_action": "Fix the status code.",
                    "evidence": [{"source": "technical", "observed": 500, "expected": 200}],
                }
            ]
        },
        "content_quality": {
            "findings": [
                {
                    "id": "content.thin",
                    "title": "Thin content",
                    "severity": "medium",
                    "page_url": "https://example.com/guide",
                    "risk": "The page may not answer the intended query completely.",
                    "next_action": "Expand original content with cited evidence.",
                }
            ]
        },
        "entity_readiness": {
            "findings": [
                {
                    "id": "entity.missing_primary_entity",
                    "title": "Missing primary entity",
                    "severity": "high",
                    "page_url": "https://example.com/guide",
                    "risk": "Entity focus is unclear.",
                    "next_action": "Clarify the primary entity.",
                    "evidence": [{"source": "entity_readiness", "observed": "No primary entity"}],
                }
            ]
        },
        "main_content": {"pages": [{"page_url": "https://example.com/guide", "title": "Guide"}]},
        "internal_links": {"findings": []},
        "search_console": {"aggregate": {"rows": 2, "clicks": 3, "impressions": 100}},
        "opportunities": {
            "opportunities": [
                {
                    "id": "opportunity.1",
                    "finding_id": "entity.missing_primary_entity",
                    "source": "entity_readiness",
                    "type": "entity",
                    "page_url": "https://example.com/guide",
                    "title": "Missing primary entity",
                    "priority": "high",
                    "risk": "Entity focus is unclear.",
                    "next_action": "Clarify the primary entity.",
                    "evidence": [{"source": "entity_readiness", "observed": "No primary entity"}],
                }
            ]
        },
        "content_briefs": {
            "briefs": [
                {
                    "id": "content_brief.entity_seo",
                    "target_url": "https://example.com/guide",
                    "priority": "high",
                    "source_opportunity_ids": ["opportunity.1"],
                    "risks_and_next_actions": [
                        {
                            "source_id": "opportunity.1",
                            "source_type": "opportunity",
                            "risk": "Entity focus is unclear.",
                            "next_action": "Update the content brief.",
                        }
                    ],
                }
            ]
        },
        "content_clusters": {
            "clusters": [
                {
                    "id": "content_cluster.entity-seo",
                    "internal_link_recommendations": [
                        {
                            "source_url": "https://example.com/guide",
                            "target_url": "https://example.com/checklist",
                            "reason": "Connect supporting checklist.",
                        }
                    ],
                    "source_opportunity_ids": ["opportunity.1"],
                }
            ]
        },
        "ai_readiness": {
            "summary": {
                "total_targets": 1,
                "average_readiness_score": 52.0,
                "by_readiness_band": {"limited": 1},
                "by_priority": {"high": 1},
            },
            "findings": [
                {
                    "target_id": "ai.page.guide",
                    "page_url": "https://example.com/guide",
                    "priority": "high",
                    "readiness_band": "limited",
                    "source_ids": ["content_brief.entity_seo", "opportunity.1"],
                    "limitations": ["AI readiness is simulated from local evidence only."],
                    "risks_and_next_actions": [
                        {
                            "priority": "high",
                            "risk": "Evidence support is incomplete.",
                            "next_action": "Add verifiable supporting evidence.",
                        }
                    ],
                }
            ],
        },
    }
