from __future__ import annotations

from pydantic import BaseModel, Field


class AudienceDistributionConfig(BaseModel):
    distribution_id: str
    name: str
    source: str
    source_notes: list[str] = Field(default_factory=list)
    sample_size: int | None = None
    platform_type: str
    categorical_distributions: dict[str, dict[str, float]] = Field(default_factory=dict)
    bernoulli_distributions: dict[str, float] = Field(default_factory=dict)
    beta_distributions: dict[str, tuple[float, float]] = Field(default_factory=dict)
    dirichlet_distributions: dict[str, list[float]] = Field(default_factory=dict)
    platform_feed_weights: dict[str, float] = Field(default_factory=dict)
    confidence: float
