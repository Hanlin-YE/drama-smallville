from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.evidence import PersonaEvidence


class SampledAudience(BaseModel):
    sample_id: str
    age_group: str | None = None
    city_tier: str | None = None
    watch_frequency: str
    repeat_watch: bool
    platform_type: str
    genre_preferences: dict[str, float] = Field(default_factory=dict)
    behavior_propensities: dict[str, float] = Field(default_factory=dict)
    content_needs: dict[str, float] = Field(default_factory=dict)


class RepresentativeAgentProfile(BaseModel):
    agent_id: str
    name: str
    archetype: str
    cluster_size: int
    segment_weight: float
    centroid_features: dict[str, float] = Field(default_factory=dict)
    categorical_summary: dict[str, dict[str, float]] = Field(default_factory=dict)
    content_needs: dict[str, float] = Field(default_factory=dict)
    behavior_thresholds: dict[str, float] = Field(default_factory=dict)
    evidence: list[PersonaEvidence] = Field(default_factory=list)
    confidence: float


class AgentProfileSet(BaseModel):
    profile_set_id: str
    platform_type: str
    business_goal: str
    representative_agents: list[RepresentativeAgentProfile]
    distribution_id: str
    population_fit: "PopulationFitReport"


class PopulationFitReport(BaseModel):
    target_distribution: dict
    representative_distribution: dict
    distribution_error: float
    max_feature_error: dict[str, float] = Field(default_factory=dict)
    accepted: bool
    confidence_level: str


AgentProfileSet.model_rebuild()

