from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StoryMaterials(BaseModel):
    character_bible: str | None = None
    world_setting: str | None = None
    previous_synopsis: str | None = None
    current_draft: str | None = None
    author_intent: str | None = None
    author_style: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class GenerationRequest(BaseModel):
    chapter_position: Literal[
        "opening",
        "early_hook",
        "mid_serial",
        "paid_conversion_point",
        "climax",
        "ending",
    ] = "early_hook"
    chapter_index: int | None = None
    episode_index: int | None = None
    desired_candidate_count: int = Field(default=3, ge=1, le=5)
    target_output: Literal["plot_direction", "chapter_draft", "short_drama_scene"] = "plot_direction"
    must_keep_elements: list[str] = Field(default_factory=list)
    avoid_elements: list[str] = Field(default_factory=list)


class StoryProjectInput(BaseModel):
    project_id: str = "demo_project"
    title: str
    format: Literal["web_novel", "short_drama", "comic_script"] = "short_drama"
    platform_type: Literal[
        "fanqie",
        "qidian",
        "jinjiang",
        "douyin_short_drama",
        "kuaishou_short_drama",
        "wechat_minidrama",
        "other",
    ] = "wechat_minidrama"
    genre: list[str] = Field(default_factory=list)
    business_goal: Literal[
        "retention",
        "positive_review",
        "paid_conversion",
        "platform_recommendation",
    ] = "paid_conversion"
    materials: StoryMaterials
    generation_request: GenerationRequest = Field(default_factory=GenerationRequest)

