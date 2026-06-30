from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from schemas.creative_review import CreativeReview
from schemas.draft import CandidateDraft
from schemas.judgment import AudienceJudgment
from schemas.message import AgentMessage
from schemas.project import StoryProjectInput
from schemas.quality import DraftQualityScore
from schemas.report import StorySimulationReport
from schemas.world_state import StoryWorldState


class TraceRecord(BaseModel):
    simulation_id: str
    schema_version: str
    input: StoryProjectInput
    story_world_state: StoryWorldState
    candidate_drafts: list[CandidateDraft]
    creative_reviews: list[CreativeReview]
    audience_judgments: list[AudienceJudgment]
    agent_messages: list[AgentMessage] = Field(default_factory=list)
    quality_scores: list[DraftQualityScore]
    final_report: StorySimulationReport
    model_settings: dict = Field(default_factory=dict)
    prompt_versions: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
