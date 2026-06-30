from __future__ import annotations

from pydantic import BaseModel, Field


class Character(BaseModel):
    name: str
    role: str = ""
    traits: list[str] = Field(default_factory=list)


class Relationship(BaseModel):
    source: str
    target: str
    relation: str
    tension: str | None = None


class StoryWorldState(BaseModel):
    project_id: str
    title: str
    genre: list[str] = Field(default_factory=list)
    platform_type: str
    chapter_position: str
    main_characters: list[Character] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    current_conflict: str
    unresolved_hooks: list[str] = Field(default_factory=list)
    emotional_debts: list[str] = Field(default_factory=list)
    hidden_information: list[str] = Field(default_factory=list)
    power_dynamics: list[str] = Field(default_factory=list)
    author_intent: str | None = None
    author_style: list[str] = Field(default_factory=list)
    platform_context: dict = Field(default_factory=dict)

