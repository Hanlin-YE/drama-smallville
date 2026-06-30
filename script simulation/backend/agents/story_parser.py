from __future__ import annotations

import re

from schemas.project import StoryProjectInput
from schemas.world_state import Character, Relationship, StoryWorldState


def parse_story_world(input_data: StoryProjectInput) -> StoryWorldState:
    materials = input_data.materials
    story_source = "\n".join(
        part
        for part in [
            materials.character_bible or "",
            materials.world_setting or "",
            materials.previous_synopsis or "",
            materials.current_draft or "",
        ]
        if part
    )
    analysis_source = "\n".join(
        part
        for part in [
            story_source,
            materials.author_intent or "",
            " ".join(materials.constraints),
        ]
        if part
    )
    names = _extract_character_names(materials.character_bible or story_source)
    characters = [
        Character(name=name, role=_guess_role(name, analysis_source), traits=_guess_traits(name, analysis_source))
        for name in names[:6]
    ]
    if not characters:
        characters = [
            Character(name="女主", role="protagonist", traits=["目标明确"]),
            Character(name="男主", role="lead", traits=["关键关系人物"]),
            Character(name="反派", role="antagonist", traits=["制造冲突"]),
        ]

    relationships = []
    if len(characters) >= 2:
        relationships.append(
            Relationship(
                source=characters[0].name,
                target=characters[1].name,
                relation="情感/利益纠葛",
                tension="信任不足或信息不对称",
            )
        )

    conflict = materials.current_draft or materials.previous_synopsis or "当前冲突尚不明确"
    return StoryWorldState(
        project_id=input_data.project_id,
        title=input_data.title,
        genre=input_data.genre,
        platform_type=input_data.platform_type,
        chapter_position=input_data.generation_request.chapter_position,
        main_characters=characters,
        relationships=relationships,
        current_conflict=_shorten(conflict, 160),
        unresolved_hooks=_extract_hooks(analysis_source),
        emotional_debts=_extract_emotional_debts(analysis_source),
        hidden_information=_extract_hidden_information(analysis_source),
        power_dynamics=_extract_power_dynamics(analysis_source),
        author_intent=materials.author_intent,
        author_style=materials.author_style,
        platform_context={
            "business_goal": input_data.business_goal,
            "format": input_data.format,
            "target_output": input_data.generation_request.target_output,
        },
    )


def _extract_character_names(text: str) -> list[str]:
    candidates = re.findall(r"[\u4e00-\u9fa5]{2,4}", text)
    stop = {"当前剧情", "作者希望", "人物设定", "世界观", "前文梗概", "候选剧情"}
    seen: list[str] = []
    for item in candidates:
        if item in stop:
            continue
        if any(token in item for token in ["女主", "男主", "反派", "养父", "儿子"]):
            if item not in seen:
                seen.append(item)
    return seen


def _guess_role(name: str, text: str) -> str:
    if "女主" in name:
        return "protagonist"
    if "男主" in name:
        return "lead"
    if "反派" in name or "养父" in name:
        return "antagonist"
    if "儿子" in name or "孩子" in name:
        return "hook_character"
    return "character"


def _guess_traits(name: str, text: str) -> list[str]:
    traits: list[str] = []
    if "强" in text or "清醒" in text:
        traits.append("清醒强势")
    if "复仇" in text:
        traits.append("复仇动机")
    if "隐瞒" in text or "真相" in text:
        traits.append("信息差相关")
    return traits or ["待补充"]


def _extract_hooks(text: str) -> list[str]:
    hooks = []
    for key in ["真相", "幕后黑手", "身份", "孩子", "证据", "反杀"]:
        if key in text:
            hooks.append(f"{key}尚未完全兑现")
    return hooks or ["下一步剧情钩子待强化"]


def _extract_emotional_debts(text: str) -> list[str]:
    debts = []
    for key in ["羞辱", "隐瞒", "误会", "背叛", "受委屈"]:
        if key in text:
            debts.append(f"{key}需要情绪兑现")
    return debts or ["情绪债待明确"]


def _extract_hidden_information(text: str) -> list[str]:
    return [f"{key}信息未公开" for key in ["真相", "身份", "证据"] if key in text] or ["隐藏信息待明确"]


def _extract_power_dynamics(text: str) -> list[str]:
    dynamics = []
    if "养父" in text:
        dynamics.append("养父掌握家族/舆论压力")
    if "男主" in text:
        dynamics.append("男主拥有资源但信任受损")
    if "女主" in text:
        dynamics.append("女主需要保持主动性")
    return dynamics or ["权力关系待明确"]


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "..."
