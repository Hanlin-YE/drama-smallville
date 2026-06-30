from __future__ import annotations

from pydantic import BaseModel


class CreativeReview(BaseModel):
    agent_id: str
    draft_id: str
    score: float
    opinion: str
    suggested_revision: str
    must_fix: bool
    author_intent_conflict: bool

