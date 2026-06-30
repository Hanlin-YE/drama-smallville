"""剧本医生 Role：对编剧的草稿做剧作评审 + 调 ScriptMind /api/generate 拿改稿建议。

调通时用 LLM 返回的 suggestions 增强评审；ScriptMind 不可达时降级到规则评审。
评审维度：连贯性（人设/伏笔/动机）+ 节奏（爽点/钩子/付费卡点）。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from schemas.creative_review import CreativeReview
from schemas.draft import CandidateDraft
from schemas.world_state import StoryWorldState

if TYPE_CHECKING:
    from llm.gateway import LLMGateway

logger = logging.getLogger(__name__)


def run_creative_reviews(
    world: StoryWorldState,
    drafts: list[CandidateDraft],
    gateway: "LLMGateway | None" = None,
) -> list[CreativeReview]:
    """剧本医生对每套草稿做连贯性 + 节奏双维度评审。

    gateway 传入时尝试调 ScriptMind /api/generate 拿 LLM 改稿建议，
    用 LLM 的 suggestions 覆盖规则的 suggested_revision；
    不可达或失败则纯规则评审。
    """
    reviews: list[CreativeReview] = []
    for draft in drafts:
        cont = _continuity_review(world, draft)
        pac = _pacing_review(world, draft)
        # 用 ScriptMind /api/extract-features 分析草稿特征，增强评审
        if gateway is not None:
            _enhance_with_scriptmind(gateway, draft, [cont, pac])
        reviews.append(cont)
        reviews.append(pac)
    return reviews


def _enhance_with_scriptmind(
    gateway: "LLMGateway",
    draft: CandidateDraft,
    reviews: list[CreativeReview],
) -> None:
    """调 /api/extract-features 拿草稿语义特征，增强 must_fix 的 review。

    /api/generate 需要 SimulationResult（试播后才有），不适合剧本医生（试播前审稿）。
    /api/extract-features 只需 50+ 字文本，返回 hookDensity/emotionVolatility/
    controversyScore 等，正好补强节奏和连贯性评审。
    """
    try:
        # 拼接 50+ 字文本（synopsis + key_beats + intended_hook）
        text_parts = [draft.synopsis, " ".join(draft.key_beats), draft.intended_hook]
        text = "。".join(p for p in text_parts if p)
        if len(text) < 50:
            logger.info("剧本医生: 草稿文本不足 50 字（%d），跳过 extract-features", len(text))
            return

        features = gateway.extract_content_features(text)
        if not features:
            logger.info("剧本医生: ScriptMind /api/extract-features 不可达，用规则评审")
            return

        logger.info(
            "剧本医生: ScriptMind 返回 hookDensity=%.2f controversyScore=%.2f",
            features.get("hook_density", 0),
            features.get("controversy_score", 0),
        )
        # 用特征增强 must_fix review 的 suggested_revision
        hook_density = features.get("hook_density", 0.5)
        controversy = features.get("controversy_score", 0.5)
        peak = features.get("peak_intensity", 0.5)
        for r in reviews:
            if not r.must_fix:
                continue
            extra: list[str] = []
            if hook_density < 0.4:
                extra.append(f"语义分析显示钩子密度偏低({hook_density:.2f})，建议强化章末悬念")
            if controversy > 0.7:
                extra.append(f"争议度偏高({controversy:.2f})，需确认争议在可接受范围")
            if peak > 0.8 and r.agent_id == "creative_pacing":
                extra.append(f"情绪峰值很高({peak:.2f})，注意不要在本集完全释放")
            if extra:
                r.suggested_revision = f"{r.suggested_revision}｜ScriptMind 补充：{'；'.join(extra)}"
    except Exception as exc:
        logger.warning("剧本医生: ScriptMind /api/extract-features 失败，用规则评审: %s", exc)


def _continuity_review(world: StoryWorldState, draft: CandidateDraft) -> CreativeReview:
    conflict = False
    opinion = "该方案基本延续当前冲突。"
    suggestion = "保留当前人物动机，并在关键行动前补一处可见线索。"
    if world.author_intent and "不要" in world.author_intent and "原谅" in world.author_intent and "原谅" in draft.synopsis:
        conflict = True
        opinion = "该方案可能违背作者「不立刻原谅」的表达意图。"
        suggestion = "把关系摊牌改为信息交换，不要让主角立即情感让步。"
    if "反杀" in draft.synopsis and "证据" in draft.synopsis:
        opinion = "该方案保留主角主动性，但需要提前铺设证据来源。"
        suggestion = "在上一场或本场前半段加入主角发现线索或布置后手。"
    return CreativeReview(
        agent_id="creative_continuity",
        draft_id=draft.draft_id,
        score=72 if conflict else 84,
        opinion=opinion,
        suggested_revision=suggestion,
        must_fix=conflict or "反杀" in draft.synopsis,
        author_intent_conflict=conflict,
    )


def _pacing_review(world: StoryWorldState, draft: CandidateDraft) -> CreativeReview:
    score = 70
    opinion = "节奏较稳，但钩子需要更明确。"
    suggestion = "章末保留一个未揭露的关键信息。"
    if draft.expected_reader_action == "pay_to_unlock":
        score = 88
        opinion = "该方案冲突强、卡点明确，适合付费节点。"
        suggestion = "不要在本集完全揭露证据，只露出足以证明主角有后手的半个信息。"
    elif "摊牌" in draft.title:
        score = 62
        opinion = "情感张力存在，但过早解释会削弱下一集钩子。"
        suggestion = "延后完整解释，只让角色承认一部分旧事。"
    return CreativeReview(
        agent_id="creative_pacing",
        draft_id=draft.draft_id,
        score=score,
        opinion=opinion,
        suggested_revision=suggestion,
        must_fix=score < 70,
        author_intent_conflict=False,
    )

