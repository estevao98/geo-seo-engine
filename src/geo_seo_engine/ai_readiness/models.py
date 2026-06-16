from __future__ import annotations

from typing import Literal

from pydantic import Field

from geo_seo_engine.core.models import CoreModel, Evidence


ReadinessBand = Literal["strong", "moderate", "limited", "not_ready"]
ReadinessPriority = Literal["critical", "high", "medium", "low"]
ReadinessTargetType = Literal["page", "cluster"]


class AIReadinessComponentScore(CoreModel):
    score: int = Field(ge=0, le=100)
    signals: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class AIReadinessRiskAction(CoreModel):
    priority: ReadinessPriority
    risk: str
    next_action: str
    source_ids: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class AIReadinessFinding(CoreModel):
    target_id: str
    target_type: ReadinessTargetType
    page_url: str | None = None
    cluster_id: str | None = None
    readiness_score: int = Field(ge=0, le=100)
    readiness_band: ReadinessBand
    priority: ReadinessPriority
    answerability: AIReadinessComponentScore
    entity_clarity: AIReadinessComponentScore
    evidence_support: AIReadinessComponentScore
    structured_data: AIReadinessComponentScore
    content_completeness: AIReadinessComponentScore
    internal_context: AIReadinessComponentScore
    risks_and_next_actions: list[AIReadinessRiskAction] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)


class AIReadinessSummary(CoreModel):
    total_targets: int = Field(default=0, ge=0)
    page_targets: int = Field(default=0, ge=0)
    cluster_targets: int = Field(default=0, ge=0)
    by_readiness_band: dict[str, int] = Field(default_factory=dict)
    by_priority: dict[str, int] = Field(default_factory=dict)
    average_readiness_score: float = Field(default=0.0, ge=0.0, le=100.0)
    inputs_present: list[str] = Field(default_factory=list)
    inputs_missing: list[str] = Field(default_factory=list)


class AIReadinessSimulationResult(CoreModel):
    findings: list[AIReadinessFinding] = Field(default_factory=list)
    summary: AIReadinessSummary
