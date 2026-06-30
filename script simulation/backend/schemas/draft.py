from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CandidateDraft(BaseModel):
    draft_id: str
    title: str
    synopsis: str
    script_text: str | None = None
    key_beats: list[str] = Field(default_factory=list)
    intended_hook: str
    intended_emotion: str
    expected_reader_action: Literal[
        "continue_reading",
        "give_positive_review",
        "pay_to_unlock",
        "comment",
        "share",
    ] = "continue_reading"
    locked_by_author: bool = False
    author_note: str | None = None

