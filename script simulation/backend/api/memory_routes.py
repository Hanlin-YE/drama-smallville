from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from memory.memory_store import append_pattern, get_memory

router = APIRouter(prefix="/api/agents", tags=["agent-memory"])


class MemoryPatternInput(BaseModel):
    description: str
    applies_to_platforms: list[str] = Field(default_factory=list)
    applies_to_genres: list[str] = Field(default_factory=list)
    signal: str | None = None
    expected_metric_effect: dict[str, float] = Field(default_factory=dict)
    negative_conditions: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


@router.get("/{agent_id}/memory")
def agent_memory(agent_id: str) -> dict[str, Any]:
    return get_memory(agent_id)


@router.post("/{agent_id}/memory/patterns")
def add_memory_pattern(agent_id: str, pattern: MemoryPatternInput) -> dict[str, Any]:
    return append_pattern(agent_id, pattern.model_dump(mode="json"))

