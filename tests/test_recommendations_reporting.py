from geo_seo_engine.reporting.recommendations import recommend_issue, recommend_issues


def test_recommend_missing_canonical():
    result = recommend_issue("page.missing_canonical")

    assert "canonical" in result.action.lower()
    assert result.issue == "page.missing_canonical"


def test_recommend_sitemap_status_not_200():
    result = recommend_issue("sitemap.status_code_not_200: 404")

    assert "sitemap" in result.action.lower()
    assert "200" in result.action


def test_recommend_issues_returns_all_items():
    result = recommend_issues(
        [
            "page.missing_canonical",
            "page.missing_meta_description",
        ]
    )

    assert len(result) == 2
    assert result[0].issue == "page.missing_canonical"


def test_recommend_issues_sorts_by_severity():
    result = recommend_issues(
        [
            "robots.robots_txt_4xx_assumed_no_restrictions",
            "page.missing_meta_description",
            "page.missing_canonical",
            "page.meta_robots_noindex",
        ]
    )

    assert [item.issue for item in result] == [
        "page.meta_robots_noindex",
        "page.missing_canonical",
        "page.missing_meta_description",
        "robots.robots_txt_4xx_assumed_no_restrictions",
    ]


def test_recommend_robots_4xx_assumed_no_restrictions():
    result = recommend_issue("robots.robots_txt_4xx_assumed_no_restrictions")

    assert "robots.txt" in result.action
    assert "rastre" in result.rationale.lower()


def test_recommend_structured_data_issues():
    missing = recommend_issue("structured_data.missing")
    invalid = recommend_issue("structured_data.invalid_json_ld")
    missing_type = recommend_issue("structured_data.missing_type")

    assert "JSON-LD" in missing.action
    assert "sintaxe" in invalid.action.lower()
    assert "@type" in missing_type.action
