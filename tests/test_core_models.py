from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from geo_seo_engine.core import (
    AuditRun,
    AuditSummary,
    Evidence,
    Issue,
    IssueCategory,
    Severity,
    UrlIdentity,
    legacy_issue_to_issue,
)


def test_issue_serializes_to_dict_and_json():
    issue = Issue(
        id="page.missing_canonical",
        title="Missing canonical",
        category=IssueCategory.INDEXABILITY,
        severity=Severity.HIGH,
        evidence=[Evidence(source="page")],
        confidence=0.9,
    )

    data = issue.model_dump(mode="json")
    json_data = issue.model_dump_json()

    assert data["id"] == "page.missing_canonical"
    assert data["category"] == "indexability"
    assert data["severity"] == "high"
    assert data["evidence"] == [
        {
            "source": "page",
            "selector": None,
            "value": None,
            "expected": None,
            "observed": None,
        }
    ]
    assert '"id":"page.missing_canonical"' in json_data


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_issue_confidence_must_be_between_zero_and_one(confidence):
    with pytest.raises(ValidationError):
        Issue(
            id="page.missing_canonical",
            title="Missing canonical",
            category=IssueCategory.INDEXABILITY,
            severity=Severity.HIGH,
            confidence=confidence,
        )


def test_audit_run_serializes_with_issues():
    issue = Issue(
        id="structured_data.missing",
        title="Missing",
        category=IssueCategory.STRUCTURED_DATA,
        severity=Severity.MEDIUM,
    )
    run = AuditRun(
        id="run-1",
        started_at=datetime(2026, 1, 1, tzinfo=UTC),
        tool_version="1.0.0",
        target=UrlIdentity(
            raw_url="https://example.com/",
            normalized_url="https://example.com/",
            host="example.com",
            path="/",
        ),
        issues=[issue],
        summary=AuditSummary(
            total_issues=1,
            by_severity={"medium": 1},
            by_category={"structured_data": 1},
        ),
    )

    data = run.model_dump(mode="json")

    assert data["started_at"] == "2026-01-01T00:00:00Z"
    assert data["issues"][0]["id"] == "structured_data.missing"
    assert data["summary"]["total_issues"] == 1


def test_legacy_issue_to_issue_for_page_missing_canonical():
    issue = legacy_issue_to_issue("page", "missing_canonical")

    assert issue.id == "page.missing_canonical"
    assert issue.title == "Missing canonical"
    assert issue.category == "indexability"
    assert issue.severity == "high"
    assert issue.evidence == []
    assert issue.recommendation is not None
    assert issue.recommendation.issue_id == "page.missing_canonical"
    assert issue.next_action is not None


def test_legacy_issue_to_issue_for_structured_data_missing():
    issue = legacy_issue_to_issue("structured_data", "missing")

    assert issue.id == "structured_data.missing"
    assert issue.title == "Missing"
    assert issue.category == "structured_data"
    assert issue.severity == "medium"
    assert issue.evidence == []
