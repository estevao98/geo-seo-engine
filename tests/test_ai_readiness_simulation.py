from geo_seo_engine.ai_readiness import run_ai_readiness_simulation


def test_ai_readiness_scores_complete_page_and_preserves_evidence():
    payload = {
        "main_content": {
            "pages": [
                {
                    "page_url": "https://example.com/docs/ai-seo",
                    "title": "AI SEO Guide",
                    "meta_description": "A practical AI SEO guide.",
                    "headings": [{"level": 1, "text": "AI SEO Guide"}, {"level": 2, "text": "Evidence"}],
                    "word_count": 900,
                    "paragraph_count": 6,
                    "heading_count": 2,
                }
            ]
        },
        "entity_readiness": {
            "page_audits": [
                {
                    "page_url": "https://example.com/docs/ai-seo",
                    "primary_entity": "AI SEO",
                    "topic_terms": ["generative search", "structured data"],
                    "title_h1_aligned": True,
                    "meta_content_aligned": True,
                    "structured_data_content_aligned": True,
                    "structured_data": {"has_organization": True, "has_article": True},
                }
            ],
            "findings": [
                {
                    "id": "entity.good",
                    "page_url": "https://example.com/docs/ai-seo",
                    "severity": "low",
                    "risk": "Minor entity ambiguity.",
                    "next_action": "Clarify related entities.",
                    "evidence": [{"source": "entity", "selector": "h1", "observed": "AI SEO Guide"}],
                }
            ],
        },
        "structured_data": {"valid_json_ld_blocks": 1, "invalid_json_ld_blocks": 0, "types": ["Article", "WebPage"]},
        "content_briefs": {
            "briefs": [
                {
                    "id": "brief.ai-seo",
                    "target_url": "https://example.com/docs/ai-seo",
                    "questions_to_answer": ["What is AI SEO?"],
                    "required_sections": ["Definition", "Evidence"],
                    "content_gaps": ["Add examples"],
                    "evidence": [{"source": "brief", "observed": "What is AI SEO?"}],
                }
            ]
        },
        "internal_links": {
            "pages": [
                {
                    "normalized_url": "https://example.com/docs/ai-seo",
                    "inbound_internal_links": 3,
                    "outbound_internal_links": 4,
                    "is_orphan": False,
                }
            ]
        },
    }

    result = run_ai_readiness_simulation(payload)

    assert result.summary.total_targets == 1
    finding = result.findings[0]
    assert finding.readiness_band in {"moderate", "strong"}
    assert finding.readiness_score >= 70
    assert "entity.good" in finding.source_ids
    assert "brief.ai-seo" in finding.source_ids
    assert finding.evidence[0].source == "entity"
    assert any("deterministic local structural simulation" in item for item in finding.limitations)


def test_ai_readiness_handles_missing_optional_inputs():
    result = run_ai_readiness_simulation({"main_content": {"pages": []}})

    assert result.summary.total_targets == 0
    assert "main_content" in result.summary.inputs_present
    assert "structured_data" in result.summary.inputs_missing


def test_ai_readiness_supports_cluster_targets():
    payload = {
        "main_content": {
            "pages": [
                {"page_url": "https://example.com/a", "title": "Topic A", "word_count": 500, "heading_count": 2},
                {"page_url": "https://example.com/b", "title": "Topic B", "word_count": 500, "heading_count": 2},
            ]
        },
        "content_clusters": {
            "clusters": [
                {
                    "id": "cluster.topic",
                    "pillar_page_url": "https://example.com/a",
                    "supporting_page_urls": ["https://example.com/b"],
                    "entities": ["Topic"],
                    "topics": ["Topic A"],
                    "source_page_ids": ["page.a", "page.b"],
                    "evidence": [{"source": "cluster", "observed": "Topic"}],
                }
            ]
        },
        "internal_links": {"edges": [{"source_url": "https://example.com/a", "target_url": "https://example.com/b"}]},
    }

    result = run_ai_readiness_simulation(payload)

    assert result.summary.page_targets == 2
    assert result.summary.cluster_targets == 1
    cluster = [item for item in result.findings if item.target_type == "cluster"][0]
    assert cluster.cluster_id == "cluster.topic"
    assert "page.a" in cluster.source_ids
    assert cluster.evidence[0].source == "cluster"
