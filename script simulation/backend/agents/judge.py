from __future__ import annotations

from schemas.creative_review import CreativeReview
from schemas.draft import CandidateDraft
from schemas.judgment import AudienceJudgment
from schemas.message import AgentMessage
from schemas.quality import DraftQualityScore
from schemas.report import StorySimulationReport
from simulation.story_environment import StoryEnvironment


def build_report(
    simulation_id: str,
    business_goal: str,
    drafts: list[CandidateDraft],
    quality_scores: list[DraftQualityScore],
    creative_reviews: list[CreativeReview],
    audience_judgments: list[AudienceJudgment],
    critic_message: AgentMessage,
    env_by_draft: dict[str, StoryEnvironment],
) -> StorySimulationReport:
    if not quality_scores:
        return StorySimulationReport(
            simulation_id=simulation_id,
            recommended_draft_id=None,
            initial_winner_draft_id=None,
            winner_changed=False,
            confidence_score=0.2,
            quality_scores=[],
            candidate_drafts=drafts,
            creative_reviews=creative_reviews,
            audience_judgments=audience_judgments,
            biggest_dropoff_risk="无可用候选稿。",
            strongest_paid_trigger="无。",
            platform_recommendation_summary="无。",
            confidence_level="low",
            confidence_reasons=["没有质量评分结果。"],
            no_strong_recommendation=True,
            next_iteration_prompt="请补充候选剧情或前文上下文。",
        )

    initial = _initial_winner(audience_judgments)
    final = quality_scores[0]
    confidence = _confidence(quality_scores, audience_judgments)
    low_confidence = confidence < 0.52 or final.final_score < 0.52
    key_disagreements = _key_disagreements(creative_reviews, audience_judgments)
    biggest_dropoff = _biggest_dropoff(audience_judgments)
    strongest_paid = _strongest_paid(audience_judgments)
    platform_summary = _platform_summary(env_by_draft, final.draft_id)
    recommendations = _rewrite_recommendations(final, creative_reviews, critic_message)

    report = StorySimulationReport(
        simulation_id=simulation_id,
        recommended_draft_id=None if low_confidence else final.draft_id,
        initial_winner_draft_id=initial,
        winner_changed=bool(initial and initial != final.draft_id),
        confidence_score=confidence,
        quality_scores=quality_scores,
        candidate_drafts=drafts,
        creative_reviews=creative_reviews,
        audience_judgments=audience_judgments,
        key_disagreements=key_disagreements,
        biggest_dropoff_risk=biggest_dropoff,
        strongest_paid_trigger=strongest_paid,
        platform_recommendation_summary=platform_summary,
        confidence_level="high" if confidence >= 0.72 else "medium" if confidence >= 0.52 else "low",
        confidence_reasons=_confidence_reasons(confidence, quality_scores, key_disagreements),
        no_strong_recommendation=low_confidence,
        rewrite_recommendations=recommendations,
        next_iteration_prompt=_next_prompt(final, recommendations, business_goal),
    )
    report.markdown = render_markdown_report(report, critic_message)
    return report


def render_markdown_report(report: StorySimulationReport, critic_message: AgentMessage) -> str:
    if report.no_strong_recommendation:
        header = "## 当前无强推荐方案"
    else:
        header = f"## 推荐方案：{report.recommended_draft_id}"
    lines = [
        header,
        "",
        f"- 初始最高分：{report.initial_winner_draft_id or '无'}",
        f"- 最终推荐：{report.recommended_draft_id or '无强推荐'}",
        f"- 置信度：{report.confidence_level} ({report.confidence_score:.2f})",
        f"- 最大弃坑风险：{report.biggest_dropoff_risk}",
        f"- 最强付费触发：{report.strongest_paid_trigger}",
        f"- 平台推荐摘要：{report.platform_recommendation_summary}",
        "",
        "### Critic 风险",
        critic_message.content,
        "",
        "### 改稿建议",
    ]
    lines.extend(f"- {item}" for item in report.rewrite_recommendations)
    lines.extend(
        [
            "",
            "> P0 评分为启发式规则，不代表真实市场统计；后续需要用真实完播率、付费率、评论数据校准。",
        ]
    )
    return "\n".join(lines)


def _initial_winner(judgments: list[AudienceJudgment]) -> str | None:
    scores: dict[str, list[float]] = {}
    for item in judgments:
        if item.round_id != "round_1":
            continue
        scores.setdefault(item.draft_id, []).append((item.continue_watch + item.pay + item.positive_review) / 3)
    if not scores:
        return None
    return max(scores, key=lambda draft_id: sum(scores[draft_id]) / len(scores[draft_id]))


def _confidence(quality_scores: list[DraftQualityScore], judgments: list[AudienceJudgment]) -> float:
    if not quality_scores:
        return 0.2
    top = quality_scores[0].final_score
    gap = top - (quality_scores[1].final_score if len(quality_scores) > 1 else 0.45)
    avg_agent_conf = sum(x.confidence for x in judgments) / max(1, len(judgments))
    return round(max(0.1, min(0.95, 0.45 * top + 0.35 * avg_agent_conf + 0.20 * min(1, gap * 4))), 3)


def _key_disagreements(reviews: list[CreativeReview], judgments: list[AudienceJudgment]) -> list[str]:
    items: list[str] = []
    for review in reviews:
        if review.must_fix:
            items.append(f"{review.draft_id}: {review.agent_id} 要求修正 - {review.opinion}")
    for judgment in judgments:
        if judgment.dropoff >= 0.55:
            items.append(f"{judgment.draft_id}: {judgment.agent_id} 弃坑风险偏高")
    return items[:5] or ["主要 Agent 分歧不强。"]


def _biggest_dropoff(judgments: list[AudienceJudgment]) -> str:
    if not judgments:
        return "无。"
    item = max(judgments, key=lambda x: x.dropoff)
    reason = item.risk_points[0] if item.risk_points else "风险未明确"
    return f"{item.draft_id} / {item.agent_id}: {reason}"


def _strongest_paid(judgments: list[AudienceJudgment]) -> str:
    if not judgments:
        return "无。"
    item = max(judgments, key=lambda x: x.pay)
    reason = item.trigger_points[0] if item.trigger_points else "付费触发未明确"
    return f"{item.draft_id} / {item.agent_id}: {reason}"


def _platform_summary(env_by_draft: dict[str, StoryEnvironment], draft_id: str) -> str:
    env = env_by_draft.get(draft_id)
    if not env:
        return "平台环境摘要不足。"
    return f"推荐信号 {env.recommendation_boost:.2f}，评论速度 {env.comment_velocity:.2f}，争议度 {env.controversy:.2f}。"


def _rewrite_recommendations(
    top: DraftQualityScore,
    reviews: list[CreativeReview],
    critic_message: AgentMessage,
) -> list[str]:
    recs = [review.suggested_revision for review in reviews if review.draft_id == top.draft_id and review.must_fix]
    if critic_message.content:
        recs.append(critic_message.content.replace("挑战 ", "处理风险："))
    if top.paid_conversion_score > 0.68:
        recs.append("保留当前付费钩子，但不要在本集完全揭露关键信息。")
    if top.character_consistency_score < 0.7:
        recs.append("补一处主角提前布置或动机说明，避免显得被动。")
    return recs[:5] or ["保持当前方案，并在章末强化下一步悬念。"]


def _confidence_reasons(confidence: float, scores: list[DraftQualityScore], disagreements: list[str]) -> list[str]:
    reasons = []
    if len(scores) > 1:
        reasons.append(f"第一名与第二名差距 {scores[0].final_score - scores[1].final_score:.2f}。")
    if disagreements and disagreements != ["主要 Agent 分歧不强。"]:
        reasons.append("存在需要处理的 Agent 分歧。")
    if confidence < 0.52:
        reasons.append("置信度偏低，建议补充材料或重写候选。")
    else:
        reasons.append("Agent 反馈和质量评分方向基本一致。")
    return reasons


def _next_prompt(top: DraftQualityScore, recommendations: list[str], goal: str) -> str:
    return (
        f"请基于 {top.draft_id} 继续改写，目标为 {goal}。优先处理："
        + "；".join(recommendations[:3])
    )
