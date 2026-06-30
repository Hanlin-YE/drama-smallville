from __future__ import annotations

from collections import defaultdict

from schemas.judgment import AudienceJudgment
from simulation.story_environment import StoryEnvironment


def build_environment(judgments: list[AudienceJudgment]) -> dict[str, StoryEnvironment]:
    grouped: dict[str, list[AudienceJudgment]] = defaultdict(list)
    for judgment in judgments:
        if judgment.round_id == "round_1":
            grouped[judgment.draft_id].append(judgment)

    env_by_draft: dict[str, StoryEnvironment] = {}
    for draft_id, items in grouped.items():
        n = max(1, len(items))
        avg_continue = sum(x.continue_watch for x in items) / n
        avg_comment = sum(x.comment for x in items) / n
        avg_positive = sum(x.positive_review for x in items) / n
        avg_drop = sum(x.dropoff for x in items) / n
        avg_pay = sum(x.pay for x in items) / n
        avg_share = sum(x.share for x in items) / n
        objections = [risk for x in items for risk in x.risk_points]
        triggers = [trigger for x in items for trigger in x.trigger_points]

        env_by_draft[draft_id] = StoryEnvironment(
            platform_heat=round(0.45 * avg_continue + 0.25 * avg_comment + 0.15 * avg_share + 0.15 * avg_pay, 3),
            comment_velocity=round(avg_comment, 3),
            positive_sentiment=round(avg_positive, 3),
            negative_sentiment=round(avg_drop, 3),
            controversy=round(min(0.98, avg_comment * 0.65 + avg_drop * 0.35), 3),
            recommendation_boost=round(
                max(0, min(0.98, 0.35 * avg_continue + 0.2 * avg_comment + 0.25 * avg_pay + 0.1 * avg_share - 0.15 * avg_drop)),
                3,
            ),
            top_comments=_sample_comments(triggers, objections),
            dominant_objections=objections[:3],
        )
    return env_by_draft


def _sample_comments(triggers: list[str], objections: list[str]) -> list[str]:
    comments = []
    if triggers:
        comments.append(f"想看后面怎么兑现：{triggers[0]}")
    if objections:
        comments.append(f"担心这里会劝退：{objections[0]}")
    return comments or ["这一段需要更明确的钩子。"]

