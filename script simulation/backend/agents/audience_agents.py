from __future__ import annotations

from schemas.draft import CandidateDraft
from schemas.judgment import AudienceJudgment
from schemas.world_state import StoryWorldState
from simulation.agent_profile import AgentProfile, P0_MARKET_AGENTS
from simulation.story_environment import StoryEnvironment


def run_round_one(
    world: StoryWorldState,
    drafts: list[CandidateDraft],
    agent_profiles: list[AgentProfile] | None = None,
) -> list[AudienceJudgment]:
    judgments: list[AudienceJudgment] = []
    profiles = agent_profiles or P0_MARKET_AGENTS
    for draft in drafts:
        for profile in profiles:
            judgments.append(_judge_draft(world, draft, profile, round_id="round_1"))
    return judgments


def run_round_two(
    world: StoryWorldState,
    drafts: list[CandidateDraft],
    round_one: list[AudienceJudgment],
    env_by_draft: dict[str, StoryEnvironment],
) -> list[AudienceJudgment]:
    revised: list[AudienceJudgment] = []
    key_agents = {"audience_paid_unlock", "platform_distribution", "audience_emotion", "paid_unlock", "platform_feed", "emotion_immersive"}
    for judgment in round_one:
        if judgment.agent_id not in key_agents:
            continue
        draft = next(d for d in drafts if d.draft_id == judgment.draft_id)
        env = env_by_draft[judgment.draft_id]
        adjusted = judgment.model_copy(deep=True)
        adjusted.round_id = "round_2"
        adjusted.revised_from_previous_round = True
        delta = 0.0
        reasons: list[str] = []
        if env.recommendation_boost > 0.7:
            delta += 0.04
            reasons.append("环境摘要显示平台推荐信号强")
        if env.controversy > 0.65 and judgment.agent_id == "audience_emotion":
            delta -= 0.03
            reasons.append("争议偏高，情感口碑风险上升")
        if env.comment_velocity > 0.65 and judgment.agent_id == "platform_distribution":
            delta += 0.03
            reasons.append("评论速度较高，利于推流")
        if "证据" in draft.synopsis and judgment.agent_id == "audience_paid_unlock":
            delta += 0.03
            reasons.append("证据未完全揭露，付费钩子增强")

        adjusted.continue_watch = _clamp(adjusted.continue_watch + delta)
        adjusted.positive_review = _clamp(adjusted.positive_review + delta / 2)
        adjusted.pay = _clamp(adjusted.pay + delta)
        adjusted.platform_recommendation = (
            _clamp((adjusted.platform_recommendation or adjusted.continue_watch) + delta)
        )
        adjusted.revision_reason = "；".join(reasons) if reasons else "读取环境摘要后保持原判断。"
        revised.append(adjusted)
    return revised


def _judge_draft(
    world: StoryWorldState,
    draft: CandidateDraft,
    profile: AgentProfile,
    round_id: str,
) -> AudienceJudgment:
    """Persona 对一个 Draft 的完整判断（编排函数，调用下面三个拆出来的函数）。"""
    text = _build_judge_text(world, draft)
    signals = _score_keywords(text, profile)
    goal = str(world.platform_context.get("business_goal", ""))
    platform_type = str(world.platform_context.get("platform_type", world.platform_type))
    scores = _apply_goal_boost(signals, goal, draft, platform_type, text)

    platform_score = None
    if profile.agent_id in {"platform_distribution", "platform_feed"}:
        platform_score = _clamp(0.35 * scores["continue_watch"] + 0.25 * scores["comment"] + 0.20 * scores["pay"] + 0.20 * scores["share"])

    triggers, risks = _generate_risks_triggers(text, profile, signals, world)

    return AudienceJudgment(
        agent_id=profile.agent_id,
        draft_id=draft.draft_id,
        round_id=round_id,
        continue_watch=scores["continue_watch"],
        positive_review=scores["positive"],
        pay=scores["pay"],
        comment=scores["comment"],
        share=scores["share"],
        dropoff=scores["dropoff"],
        platform_recommendation=platform_score,
        trigger_points=triggers,
        risk_points=risks,
        confidence=0.72,
    )


def _build_judge_text(world: StoryWorldState, draft: CandidateDraft) -> str:
    """拼接 world + draft 成供关键词匹配的文本。"""
    world_text = " ".join(
        [
            world.current_conflict,
            " ".join(world.unresolved_hooks),
            " ".join(world.emotional_debts),
            " ".join(world.hidden_information),
            " ".join(world.power_dynamics),
            str(world.platform_context.get("business_goal", "")),
        ]
    )
    return f"{draft.title} {draft.synopsis} {' '.join(draft.key_beats)} {world_text}"


def _score_keywords(text: str, profile: AgentProfile) -> dict:
    """关键词匹配 → 原始信号分数（未 clamp、未加 goal_boost）。

    返回: {match, mismatch, hook, emotion, base, continue_watch, positive, pay,
    comment, share, dropoff}
    """
    match = _keyword_match(text, profile.likes)
    mismatch = _keyword_match(text, profile.dislikes)
    hook = _keyword_match(text, ["钩子", "证据", "身份", "真相", "反杀", "危机"])
    emotion = _keyword_match(text, ["拉扯", "愧疚", "委屈", "守护", "破防", "反击"])
    platform_boost = 0.0  # platform_boost 需要实际 platform_type，在 _apply_goal_boost 里计算
    return {
        "match": match,
        "mismatch": mismatch,
        "hook": hook,
        "emotion": emotion,
        "platform_boost": platform_boost,
    }


def _apply_goal_boost(
    signals: dict,
    goal: str,
    draft: CandidateDraft,
    platform_type: str,
    text: str,
) -> dict[str, float]:
    """把关键词信号 + 商业目标 → 六维度分数（已 clamp）。"""
    match = signals["match"]
    mismatch = signals["mismatch"]
    hook = signals["hook"]
    emotion = signals["emotion"]
    goal_boost = _goal_boost(goal, draft)
    platform_boost = _platform_boost(platform_type, text)

    base = 0.48 + 0.07 * match - 0.06 * mismatch + platform_boost
    continue_watch = _clamp(base + 0.06 * hook + 0.03 * emotion)
    positive = _clamp(base + 0.05 * emotion - 0.04 * mismatch)
    pay = _clamp(base + 0.08 * hook + (0.08 if draft.expected_reader_action == "pay_to_unlock" else 0))
    comment = _clamp(base + 0.06 * _keyword_match(text, ["危机", "舆论", "羞辱", "反咬", "争议"]))
    share = _clamp(base + 0.04 * _keyword_match(text, ["反杀", "直播", "公开", "打脸"]))
    dropoff = _clamp(0.28 + 0.08 * mismatch - 0.04 * match)

    if goal == "retention":
        continue_watch = _clamp(continue_watch + goal_boost)
        dropoff = _clamp(dropoff - goal_boost / 2)
    elif goal == "positive_review":
        positive = _clamp(positive + goal_boost)
        comment = _clamp(comment + goal_boost / 2)
        if draft.expected_reader_action == "pay_to_unlock":
            pay = _clamp(pay - 0.035)
            positive = _clamp(positive - 0.06)
    elif goal == "paid_conversion":
        pay = _clamp(pay + goal_boost)
        if draft.expected_reader_action == "give_positive_review":
            continue_watch = _clamp(continue_watch - 0.02)
    elif goal == "platform_recommendation":
        comment = _clamp(comment + goal_boost / 2)
        share = _clamp(share + goal_boost)

    return {
        "continue_watch": continue_watch,
        "positive": positive,
        "pay": pay,
        "comment": comment,
        "share": share,
        "dropoff": dropoff,
    }


def _generate_risks_triggers(
    text: str,
    profile: AgentProfile,
    signals: dict,
    world: StoryWorldState,
) -> tuple[list[str], list[str]]:
    """从关键词信号生成 trigger_points 和 risk_points。"""
    match = signals["match"]
    mismatch = signals["mismatch"]
    hook = signals["hook"]

    risks: list[str] = []
    if mismatch:
        risks.append(f"可能触发{profile.name}对{','.join(profile.dislikes[:2])}的反感")
    if "原谅" in text and world.author_intent and "不要" in world.author_intent:
        risks.append("与作者不立刻原谅的意图冲突")
    if not risks:
        risks.append("如果下一段不兑现当前钩子，后续可能掉留存")

    triggers: list[str] = []
    if hook:
        triggers.append("未揭露信息形成继续看/付费动机")
    if match:
        triggers.append(f"命中{profile.name}偏好的{','.join(profile.likes[:2])}")
    if not triggers:
        triggers.append("基础冲突可支撑继续看，但需要强化钩子")

    return triggers, risks


def _goal_boost(goal: str, draft: CandidateDraft) -> float:
    action = draft.expected_reader_action
    if goal == "paid_conversion" and action == "pay_to_unlock":
        return 0.075
    if goal == "positive_review" and action == "give_positive_review":
        return 0.18
    if goal == "retention" and action == "continue_reading":
        return 0.075
    if goal == "platform_recommendation" and action in {"share", "comment"}:
        return 0.085
    return 0.015


def _platform_boost(platform_type: str, text: str) -> float:
    if platform_type in {"douyin_short_drama", "kuaishou_short_drama"}:
        return 0.025 * _keyword_match(text, ["公开", "直播", "舆论", "反杀", "强标签"])
    if platform_type == "wechat_minidrama":
        return 0.02 * _keyword_match(text, ["付费", "下一集", "证据", "真相"])
    if platform_type in {"fanqie", "qidian"}:
        return 0.018 * _keyword_match(text, ["伏笔", "长期", "身份", "世界"])
    if platform_type == "jinjiang":
        return 0.018 * _keyword_match(text, ["拉扯", "情绪", "关系", "误会"])
    return 0.0


def _keyword_match(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _clamp(value: float) -> float:
    return round(max(0.0, min(0.98, value)), 3)
