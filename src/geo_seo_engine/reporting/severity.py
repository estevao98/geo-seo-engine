from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


Severity = Literal["critical", "high", "medium", "low"]

SCORE_PENALTIES: dict[Severity, int] = {
    "critical": 30,
    "high": 15,
    "medium": 7,
    "low": 3,
}


@dataclass(frozen=True)
class IssueSeverity:
    issue: str
    severity: Severity
    reason: str


def _extract_status_code(issue: str) -> int | None:
    match = re.search(r"status_code_not_200:\s*(\d+)", issue)
    if not match:
        return None
    return int(match.group(1))


def classify_issue(issue: str) -> IssueSeverity:
    status_code = _extract_status_code(issue)

    if issue.startswith("page.status_code_not_200"):
        return IssueSeverity(
            issue=issue,
            severity="critical",
            reason="A página auditada não retornou 200, o que pode impedir rastreamento, renderização ou indexação.",
        )

    if issue.startswith("page.meta_robots_noindex"):
        return IssueSeverity(
            issue=issue,
            severity="critical",
            reason="A página contém noindex, o que pode impedir sua presença no índice.",
        )

    if issue.startswith("robots.disallow_all_found"):
        return IssueSeverity(
            issue=issue,
            severity="critical",
            reason="O robots.txt contém bloqueio amplo, o que pode impedir rastreamento de áreas importantes.",
        )

    if issue.startswith("robots.status_code_not_200"):
        if status_code is not None and 400 <= status_code < 500 and status_code != 429:
            return IssueSeverity(
                issue=issue,
                severity="low",
                reason="Erro 4xx em robots.txt, exceto 429, normalmente é tratado como ausência de robots.txt.",
            )

        return IssueSeverity(
            issue=issue,
            severity="critical",
            reason="robots.txt inacessível por 429 ou erro 5xx pode afetar rastreamento temporariamente.",
        )

    if issue.startswith("sitemap.status_code_not_200"):
        return IssueSeverity(
            issue=issue,
            severity="high",
            reason="Sitemap inacessível prejudica descoberta e validação de URLs importantes.",
        )

    if issue.startswith(
        (
            "page.missing_title",
            "page.missing_h1",
            "page.missing_canonical",
            "sitemap.no_urls_found",
            "sitemap.invalid_urls_found",
        )
    ):
        return IssueSeverity(
            issue=issue,
            severity="high",
            reason="Afeta sinais técnicos ou semânticos importantes para SEO.",
        )

    if issue.startswith(
        (
            "page.missing_meta_description",
            "sitemap.duplicate_urls_found",
            "sitemap.urls_with_query_found",
            "sitemap.off_domain_urls_found",
            "robots.unknown_or_invalid_directives_found",
        )
    ):
        return IssueSeverity(
            issue=issue,
            severity="medium",
            reason="Afeta qualidade, clareza ou eficiência de rastreamento.",
        )

    if issue.startswith(
        (
            "robots.missing_sitemap_directive",
            "robots.robots_txt_4xx_assumed_no_restrictions",
        )
    ):
        return IssueSeverity(
            issue=issue,
            severity="low",
            reason="Melhoria recomendada, mas normalmente não bloqueia indexação por si só.",
        )

    return IssueSeverity(
        issue=issue,
        severity="medium",
        reason="Issue ainda sem regra específica; classificada como prioridade intermediária.",
    )


def classify_issues(issues: list[str]) -> list[IssueSeverity]:
    return [classify_issue(issue) for issue in issues]


def severity_counts(issues: list[str]) -> dict[str, int]:
    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for classified in classify_issues(issues):
        counts[classified.severity] += 1

    return counts


def calculate_site_score(issues: list[str]) -> int:
    score = 100

    for classified in classify_issues(issues):
        score -= SCORE_PENALTIES[classified.severity]

    return max(score, 0)
