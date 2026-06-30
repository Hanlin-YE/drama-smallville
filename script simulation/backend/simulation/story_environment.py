from __future__ import annotations

from pydantic import BaseModel, Field


class StoryEnvironment(BaseModel):
    platform_heat: float = 0
    comment_velocity: float = 0
    positive_sentiment: float = 0
    negative_sentiment: float = 0
    controversy: float = 0
    recommendation_boost: float = 0
    top_comments: list[str] = Field(default_factory=list)
    dominant_objections: list[str] = Field(default_factory=list)


def build_environment_summary(env_by_draft: dict[str, StoryEnvironment]) -> str:
    lines: list[str] = []
    for draft_id, env in env_by_draft.items():
        lines.append(
            f"{draft_id}: heat={env.platform_heat:.2f}, comments={env.comment_velocity:.2f}, "
            f"positive={env.positive_sentiment:.2f}, controversy={env.controversy:.2f}, "
            f"boost={env.recommendation_boost:.2f}"
        )
        if env.top_comments:
            lines.append(f"  simulated_comments: {'；'.join(env.top_comments[:2])}")
        if env.dominant_objections:
            lines.append(f"  objections: {'；'.join(env.dominant_objections[:2])}")
    return "\n".join(lines)

