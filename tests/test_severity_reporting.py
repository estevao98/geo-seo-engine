from geo_seo_engine.reporting.severity import classify_issue, severity_counts


def test_classify_page_status_code_issue_as_critical():
    result = classify_issue("page.status_code_not_200: 500")

    assert result.severity == "critical"


def test_classify_robots_404_as_low():
    result = classify_issue("robots.status_code_not_200: 404")

    assert result.severity == "low"


def test_classify_robots_500_as_critical():
    result = classify_issue("robots.status_code_not_200: 500")

    assert result.severity == "critical"


def test_classify_sitemap_404_as_high():
    result = classify_issue("sitemap.status_code_not_200: 404")

    assert result.severity == "high"


def test_classify_missing_meta_description_as_medium():
    result = classify_issue("page.missing_meta_description")

    assert result.severity == "medium"


def test_severity_counts():
    counts = severity_counts(
        [
            "sitemap.status_code_not_200: 404",
            "page.missing_title",
            "page.missing_meta_description",
            "robots.missing_sitemap_directive",
            "robots.status_code_not_200: 404",
        ]
    )

    assert counts == {
        "critical": 0,
        "high": 2,
        "medium": 1,
        "low": 2,
    }
