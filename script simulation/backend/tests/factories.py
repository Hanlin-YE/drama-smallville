"""测试工厂函数：构造最小可用的测试对象，避免每个测试都手写十几个字段。"""

from __future__ import annotations

from schemas.draft import CandidateDraft
from schemas.world_state import Character, Relationship, StoryWorldState
from simulation.agent_profile import AgentProfile


def make_test_world(
    conflict: str = "女主发现男主隐瞒真相，但真正幕后黑手是养父",
    business_goal: str = "paid_conversion",
    platform_type: str = "douyin_short_drama",
    author_intent: str | None = "希望女主保持清醒强势，不要立刻原谅男主",
) -> StoryWorldState:
    return StoryWorldState(
        project_id="test_project",
        title="测试故事",
        genre=["suspense"],
        platform_type=platform_type,
        chapter_position="paid_conversion_point",
        main_characters=[
            Character(name="女主", role="protagonist", traits=["清醒强势"]),
            Character(name="男主", role="lead", traits=["信任受损"]),
        ],
        relationships=[
            Relationship(source="女主", target="男主", relation="情感纠葛", tension="信任不足"),
        ],
        current_conflict=conflict,
        unresolved_hooks=["身份真相尚未兑现"],
        emotional_debts=["背叛需要情绪兑现"],
        hidden_information=["养父是幕后黑手"],
        power_dynamics=["女主需要保持主动"],
        author_intent=author_intent,
        author_style=["作者驱动"],
        platform_context={"business_goal": business_goal, "platform_type": platform_type},
    )


def make_test_draft(
    draft_id: str = "draft_a",
    title: str = "反杀局",
    synopsis: str = "女主假意合作暗中设局，养父制造偷拍反咬但女主提前埋下证据反杀",
    expected_reader_action: str = "pay_to_unlock",
) -> CandidateDraft:
    return CandidateDraft(
        draft_id=draft_id,
        title=title,
        synopsis=synopsis,
        key_beats=["设局", "反击", "反杀"],
        intended_hook="证据指向谁",
        intended_emotion="危机爽感",
        expected_reader_action=expected_reader_action,
    )


def make_test_persona(
    agent_id: str = "audience_shuangwen",
    name: str = "爽点追更型观众",
    likes: list[str] | None = None,
    dislikes: list[str] | None = None,
    segment_weight: float = 0.28,
) -> AgentProfile:
    return AgentProfile(
        agent_id=agent_id,
        name=name,
        segment_weight=segment_weight,
        likes=likes or ["反杀", "打脸", "证据", "主动", "强冲突"],
        dislikes=dislikes or ["憋屈", "拖沓", "过早和解"],
        thresholds={"pay": 7.0, "dropoff": 7.2},
    )
