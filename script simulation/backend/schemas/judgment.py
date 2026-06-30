from __future__ import annotations

from pydantic import BaseModel, Field


class AudienceJudgment(BaseModel):
    agent_id: str
    draft_id: str
    round_id: str
    continue_watch: float
    positive_review: float
    pay: float
    comment: float
    share: float
    dropoff: float
    platform_recommendation: float | None = None
    trigger_points: list[str] = Field(default_factory=list)
    risk_points: list[str] = Field(default_factory=list)
    revised_from_previous_round: bool = False
    revision_reason: str | None = None
    confidence: float = 0.7

