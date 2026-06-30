from __future__ import annotations

from schemas.draft import CandidateDraft
from schemas.message import AgentMessage
from schemas.quality import DraftQualityScore


def challenge_top_draft(drafts: list[CandidateDraft], scores: list[DraftQualityScore]) -> AgentMessage:
    if not scores:
        return AgentMessage(
            message_id="critic_empty",
            round_id="critic",
            from_agent="critic",
            to_agent="judge",
            message_type="challenge",
            content="没有可挑战的候选稿。",
        )
    top = max(scores, key=lambda item: item.final_score)
    draft = next(d for d in drafts if d.draft_id == top.draft_id)
    risks = []
    if top.character_consistency_score < 0.68:
        risks.append("人物动机一致性不足")
    if top.paid_conversion_score > 0.72 and top.logic_consistency_score < 0.70:
        risks.append("付费钩子强但逻辑支撑偏弱")
    if "危机" in draft.synopsis and "反击" not in draft.synopsis:
        risks.append("危机感强，但主角主动性不足")
    if not risks:
        risks.append("最高分方案仍需确保下一集兑现当前钩子")
    return AgentMessage(
        message_id=f"critic_{top.draft_id}",
        round_id="critic",
        from_agent="critic",
        to_agent="judge",
        message_type="challenge",
        content=f"挑战 {draft.title}：{'；'.join(risks)}。",
        referenced_draft_id=top.draft_id,
        scores_delta={"risk": -0.03 if len(risks) > 1 else -0.01},
    )

