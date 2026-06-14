import json

from geo_seo_engine.content_briefs import generate_content_briefs


def test_content_brief_generator_builds_deterministic_brief_from_local_inputs():
    payload = _payload()

    first = generate_content_briefs(payload)
    second = generate_content_briefs(payload)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.summary.total_briefs == 1
    brief = first.briefs[0]
    assert brief.target_url == "https://example.com/guides/entity-seo"
    assert brief.brief_type == "risk_remediation"
    assert brief.priority == "critical"
    assert brief.primary_topic_entity_cue == "Entity SEO"
    assert brief.search_intent_cue == "informational"
    assert "opportunity.1" in brief.source_opportunity_ids
    assert "entity.missing_primary_entity" in brief.source_finding_ids
    assert brief.internal_link_opportunities[0].source_url == "https://example.com/blog/seo"
    assert any("Define the primary entity" in section for section in brief.required_sections)
    assert any("What does the user need" in question for question in brief.questions_to_answer)


def test_content_brief_generator_handles_missing_optional_inputs():
    result = generate_content_briefs(
        {
            "main_content": {
                "pages": [
                    {
                        "page_url": "https://example.com/a",
                        "title": "Example page",
                        "extraction_method": "static_html",
                        "word_count": 120,
                    }
                ]
            }
        }
    )

    assert result.summary.total_briefs == 1
    brief = result.briefs[0]
    assert brief.priority == "low"
    assert brief.source_opportunity_ids == []
    assert any("No opportunity records were available" in limitation for limitation in brief.limitations)
    assert "search_console" in result.summary.inputs_missing


def test_content_brief_generator_preserves_evidence_and_next_actions():
    result = generate_content_briefs(_payload())

    brief = result.briefs[0]
    assert brief.evidence[0].source == "entity_readiness"
    assert brief.evidence[0].observed == "No primary entity"
    assert brief.risks_and_next_actions[0].source_id == "opportunity.1"
    assert brief.risks_and_next_actions[0].next_action == "Define the primary entity and supporting terms."
    assert brief.risks_and_next_actions[0].evidence[0].expected == "Primary entity"


def test_content_brief_generator_preserves_related_finding_evidence_when_opportunity_evidence_is_empty():
    payload = _payload()
    payload["opportunities"][0]["evidence"] = []

    result = generate_content_briefs(payload)

    assert result.briefs[0].evidence[0].source == "entity_readiness"
    assert result.briefs[0].source_finding_ids == ["entity.missing_primary_entity"]


def test_content_brief_generator_json_serialization_is_stable():
    result = generate_content_briefs(_payload())

    rendered = json.dumps(result.model_dump(mode="json"), sort_keys=True)
    data = json.loads(rendered)

    assert data["briefs"][0]["confidence"] == 1.0
    assert data["summary"]["by_priority"] == {"critical": 1}


def _payload():
    return {
        "opportunities": [
            {
                "id": "opportunity.1",
                "finding_id": "entity.missing_primary_entity",
                "source": "entity_readiness",
                "type": "entity",
                "page_url": "https://example.com/guides/entity-seo",
                "title": "Missing primary entity",
                "severity": "high",
                "impact": "high",
                "effort": "low",
                "confidence": 0.9,
                "priority": "critical",
                "score": 91.0,
                "score_components": {
                    "severity": 32.0,
                    "impact": 24.0,
                    "effort": 16.0,
                    "confidence": 12.6,
                    "analytics": 6.4,
                    "total": 91.0,
                },
                "rationale": ["High impact entity gap found in local audit."],
                "evidence": [
                    {
                        "source": "entity_readiness",
                        "observed": "No primary entity",
                        "expected": "Primary entity",
                    }
                ],
                "risk": "Generative systems may not identify the page topic clearly.",
                "next_action": "Define the primary entity and supporting terms.",
            }
        ],
        "entity_readiness": {
            "page_audits": [
                {
                    "page_url": "https://example.com/guides/entity-seo",
                    "primary_entity": "Entity SEO",
                    "topic_terms": ["entities", "schema"],
                }
            ],
            "findings": [
                {
                    "id": "entity.missing_primary_entity",
                    "title": "Missing primary entity",
                    "severity": "high",
                    "category": "entity",
                    "page_url": "https://example.com/guides/entity-seo",
                    "evidence": [
                        {
                            "source": "entity_readiness",
                            "observed": "No primary entity",
                            "expected": "Primary entity",
                        }
                    ],
                    "risk": "Topic ambiguity.",
                    "next_action": "Define the primary entity and supporting terms.",
                }
            ],
        },
        "main_content": {
            "pages": [
                {
                    "page_url": "https://example.com/guides/entity-seo",
                    "title": "Entity SEO guide",
                    "extraction_method": "static_html",
                    "headings": [{"level": 1, "text": "Entity SEO", "order": 0}],
                    "word_count": 250,
                }
            ]
        },
        "internal_links": {
            "edges": [
                {
                    "source_url": "https://example.com/blog/seo",
                    "target_url": "https://example.com/guides/entity-seo",
                    "anchor_text": "entity SEO guide",
                }
            ]
        },
        "search_console": {
            "rows": [
                {
                    "query": "what is entity seo",
                    "page": "https://example.com/guides/entity-seo",
                    "normalized_page": "https://example.com/guides/entity-seo",
                    "date": "2024-01-01",
                    "country": "usa",
                    "device": "desktop",
                    "clicks": 2,
                    "impressions": 500,
                    "ctr": 0.004,
                    "position": 12.0,
                }
            ]
        },
    }
