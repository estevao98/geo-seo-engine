from __future__ import annotations

from typing import Literal

from geo_seo_engine.core.models import Issue, IssueCategory, Recommendation, Severity
from geo_seo_engine.reporting.recommendations import recommend_issue
from geo_seo_engine.reporting.severity import classify_issue


LegacyIssueSource = Literal["page", "robots", "sitemap", "structured_data"]


_SOURCE_DEFAULT_CATEGORY: dict[str, IssueCategory] = {
    "page": IssueCategory.TECHNICAL,
    "robots": IssueCategory.CRAWLABILITY,
    "sitemap": IssueCategory.CRAWLABILITY,
    "structured_data": IssueCategory.STRUCTURED_DATA,
}


def legacy_issue_to_issue(source: LegacyIssueSource, issue: str) -> Issue:
    issue_id = issue if issue.startswith(f"{source}.") else f"{source}.{issue}"
    classified = classify_issue(issue_id)
    legacy_recommendation = recommend_issue(issue_id)
    recommendation = Recommendation(
        issue_id=issue_id,
        action=legacy_recommendation.action,
        rationale=legacy_recommendation.rationale,
    )

    return Issue(
        id=issue_id,
        title=_title_from_issue(issue),
        category=_category_for_issue(source, issue_id),
        severity=Severity(classified.severity),
        risk=classified.reason,
        recommendation=recommendation,
        next_action=recommendation.action,
        confidence=0.8,
    )


def _category_for_issue(source: LegacyIssueSource, issue_id: str) -> IssueCategory:
    if issue_id.startswith(("page.meta_robots_noindex", "page.missing_canonical")):
        return IssueCategory.INDEXABILITY

    if issue_id.startswith(
        (
            "page.missing_title",
            "page.missing_meta_description",
            "page.missing_h1",
            "page.multiple_h1",
        )
    ):
        return IssueCategory.CONTENT

    return _SOURCE_DEFAULT_CATEGORY[source]


def _title_from_issue(issue: str) -> str:
    issue_name = issue.split(".", maxsplit=1)[-1]
    issue_name = issue_name.split(":", maxsplit=1)[0]
    return issue_name.replace("_", " ").strip().capitalize()
