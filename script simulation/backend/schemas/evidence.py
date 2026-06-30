from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PersonaEvidence(BaseModel):
    source_type: Literal[
        "industry_report",
        "manual_expert",
        "real_feedback",
        "comment_sample",
        "simulation",
    ]
    source_name: str
    sample_size: int | None = None
    observed_metric: dict[str, float] = Field(default_factory=dict)
    confidence: float
    note: str | None = None

