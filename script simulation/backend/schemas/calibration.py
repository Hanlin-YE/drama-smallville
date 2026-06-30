from __future__ import annotations

from pydantic import BaseModel, Field


class RealFeedback(BaseModel):
    project_id: str
    episode_id: str
    platform_type: str
    actual_retention: float | None = None
    actual_paid_conversion: float | None = None
    actual_positive_review_rate: float | None = None
    actual_comment_rate: float | None = None
    comment_keywords: list[str] = Field(default_factory=list)
    editor_notes: list[str] = Field(default_factory=list)


class CalibrationRecord(BaseModel):
    simulation_id: str
    predicted_metrics: dict[str, float]
    actual_metrics: dict[str, float]
    error_metrics: dict[str, float]
    suggested_agent_adjustments: dict = Field(default_factory=dict)
    accepted: bool = False

