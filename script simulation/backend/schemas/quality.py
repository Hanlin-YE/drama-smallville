from __future__ import annotations

from pydantic import BaseModel


class DraftQualityScore(BaseModel):
    draft_id: str
    retention_score: float
    positive_review_score: float
    paid_conversion_score: float
    platform_recommendation_score: float
    logic_consistency_score: float
    character_consistency_score: float
    hook_strength_score: float
    emotional_intensity_score: float
    disagreement_penalty: float
    final_score: float

