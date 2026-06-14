from geo_seo_engine.performance import PagePerformanceSnapshot, parse_pagespeed_result


def pagespeed_payload():
    return {
        "id": "https://example.com/",
        "loadingExperience": {
            "metrics": {
                "LARGEST_CONTENTFUL_PAINT_MS": {"percentile": 3200},
                "CUMULATIVE_LAYOUT_SHIFT_SCORE": {"percentile": 0.18},
                "INTERACTION_TO_NEXT_PAINT": {"percentile": 260},
            }
        },
        "originLoadingExperience": {
            "metrics": {
                "FIRST_CONTENTFUL_PAINT_MS": {"percentile": 1200},
            }
        },
        "lighthouseResult": {
            "requestedUrl": "https://example.com/",
            "finalUrl": "https://example.com/?utm=ignored",
            "lighthouseVersion": "12.0.0",
            "configSettings": {"formFactor": "desktop"},
            "categories": {"performance": {"score": 0.42}},
            "audits": {
                "first-contentful-paint": {
                    "title": "First Contentful Paint",
                    "numericValue": 1100,
                    "numericUnit": "millisecond",
                    "displayValue": "1.1 s",
                },
                "largest-contentful-paint": {
                    "title": "Largest Contentful Paint",
                    "numericValue": 4100,
                    "numericUnit": "millisecond",
                    "displayValue": "4.1 s",
                },
                "cumulative-layout-shift": {
                    "title": "Cumulative Layout Shift",
                    "numericValue": 0.31,
                    "numericUnit": "unitless",
                    "displayValue": "0.31",
                },
                "total-blocking-time": {
                    "title": "Total Blocking Time",
                    "numericValue": 620,
                    "numericUnit": "millisecond",
                    "displayValue": "620 ms",
                },
                "speed-index": {
                    "title": "Speed Index",
                    "numericValue": 3300,
                    "numericUnit": "millisecond",
                    "displayValue": "3.3 s",
                },
                "interaction-to-next-paint": {
                    "title": "Interaction to Next Paint",
                    "numericValue": 280,
                    "numericUnit": "millisecond",
                    "displayValue": "280 ms",
                },
                "server-response-time": {
                    "title": "Initial server response time was short",
                    "numericValue": 900,
                    "numericUnit": "millisecond",
                    "displayValue": "900 ms",
                },
                "unused-javascript": {
                    "title": "Reduce unused JavaScript",
                    "description": "Remove unused code.",
                    "score": 0.3,
                    "scoreDisplayMode": "opportunity",
                    "details": {
                        "type": "opportunity",
                        "overallSavingsMs": 1400,
                        "overallSavingsBytes": 640000,
                    },
                },
                "dom-size": {
                    "title": "Avoid an excessive DOM size",
                    "description": "Keep DOM small.",
                    "score": 0.8,
                    "details": {"type": "diagnostic"},
                },
            },
        },
    }


def test_parse_pagespeed_result_normalizes_lab_field_opportunities_and_metadata():
    snapshot = parse_pagespeed_result(pagespeed_payload())

    assert snapshot.page_url == "https://example.com/?utm=ignored"
    assert snapshot.requested_url == "https://example.com/"
    assert snapshot.final_url == "https://example.com/?utm=ignored"
    assert snapshot.strategy == "desktop"
    assert snapshot.performance_score == 42
    assert snapshot.has_lab_data is True
    assert snapshot.has_field_data is True
    assert snapshot.raw_source_version == "12.0.0"

    lab_lcp = next(metric for metric in snapshot.metrics if metric.id == "largest-contentful-paint" and metric.category == "lab")
    assert lab_lcp.value == 4100
    assert lab_lcp.display_value == "4.1 s"
    assert any(metric.source == "crux_page" for metric in snapshot.metrics)
    assert any(metric.source == "crux_origin" for metric in snapshot.metrics)
    assert snapshot.opportunities[0].id == "unused-javascript"
    assert snapshot.opportunities[0].estimated_savings_ms == 1400
    assert snapshot.diagnostics[0].id == "dom-size"


def test_parse_pagespeed_result_supports_page_url_override_and_missing_data():
    snapshot = parse_pagespeed_result({}, page_url="https://example.com/manual")

    assert snapshot == PagePerformanceSnapshot(page_url="https://example.com/manual")
    assert snapshot.has_lab_data is False
    assert snapshot.has_field_data is False
    assert snapshot.metrics == []


def test_performance_snapshot_json_serializes_stably():
    snapshot = parse_pagespeed_result(pagespeed_payload())
    data = snapshot.model_dump(mode="json")

    assert data["performance_score"] == 42
    assert data["metrics"][0]["id"] == "first-contentful-paint"
    assert data["opportunities"][0]["estimated_savings_bytes"] == 640000
