from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from schemas.creative_review import CreativeReview
from schemas.draft import CandidateDraft
from schemas.judgment import AudienceJudgment
from schemas.quality import DraftQualityScore


class StorySimulationReport(BaseModel):
    simulation_id: str
    recommended_draft_id: str | None
    initial_winner_draft_id: str | None
    winner_changed: bool
    confidence_score: float
    quality_scores: list[DraftQualityScore]
    candidate_drafts: list[CandidateDraft] = Field(default_factory=list)
    creative_reviews: list[CreativeReview]
    audience_judgments: list[AudienceJudgment]
    key_disagreements: list[str] = Field(default_factory=list)
    biggest_dropoff_risk: str
    strongest_paid_trigger: str
    platform_recommendation_summary: str
    confidence_level: Literal["high", "medium", "low"]
    confidence_reasons: list[str] = Field(default_factory=list)
    no_strong_recommendation: bool = False
    rewrite_recommendations: list[str] = Field(default_factory=list)
    next_iteration_prompt: str
    markdown: str | None = None
