from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class AgentMessage(BaseModel):
    message_id: str
    round_id: str
    from_agent: str
    to_agent: str | Literal["all"]
    message_type: Literal[
        "draft",
        "creative_review",
        "judgment",
        "environment_feedback",
        "challenge",
        "revision",
        "judge_summary",
    ]
    content: str
    referenced_draft_id: str | None = None
    scores_delta: dict[str, float] | None = None

