from __future__ import annotations

from collections import defaultdict
from statistics import pstdev

from schemas.creative_review import CreativeReview
from schemas.judgment import AudienceJudgment
from schemas.quality import DraftQualityScore


def evaluate_quality(
    business_goal: str,
    judgments: list[AudienceJudgment],
    creative_reviews: list[CreativeReview],
) -> list[DraftQualityScore]:
    by_draft: dict[str, list[AudienceJudgment]] = defaultdict(list)
    for judgment in judgments:
        if judgment.round_id in {"round_1", "round_2"}:
            by_draft[judgment.draft_id].append(judgment)

    creative_by_draft: dict[str, list[CreativeReview]] = defaultdict(list)
    for review in creative_reviews:
        creative_by_draft[review.draft_id].append(review)

    scores: list[DraftQualityScore] = []
    for draft_id, items in by_draft.items():
        retention = _avg([x.continue_watch for x in items])
        positive = _avg([x.positive_review for x in items])
        paid = _avg([x.pay for x in items])
        platform = _avg([x.platform_recommendation for x in items if x.platform_recommendation is not None] or [retention])
        emotional = _avg([x.positive_review + x.comment for x in items]) / 2
        hook = _avg([x.pay + x.continue_watch for x in items]) / 2
        creative_scores = creative_by_draft.get(draft_id, [])
        logic = _avg([x.score / 100 for x in creative_scores if x.agent_id == "creative_continuity"] or [0.72])
        character = max(0.0, logic - (0.08 if any(x.author_intent_conflict for x in creative_scores) else 0.0))
        values = [x.continue_watch for x in items] + [x.pay for x in items]
        disagreement = min(0.18, pstdev(values) if len(values) > 1 else 0)
        final = _final_score(business_goal, retention, positive, paid, platform, logic, character, hook, emotional, disagreement)
        scores.append(
            DraftQualityScore(
                draft_id=draft_id,
                retention_score=round(retention, 3),
                positive_review_score=round(positive, 3),
                paid_conversion_score=round(paid, 3),
                platform_recommendation_score=round(platform, 3),
                logic_consistency_score=round(logic, 3),
                character_consistency_score=round(character, 3),
                hook_strength_score=round(hook, 3),
                emotional_intensity_score=round(emotional, 3),
                disagreement_penalty=round(disagreement, 3),
                final_score=round(final, 3),
            )
        )
    return sorted(scores, key=lambda item: item.final_score, reverse=True)


def _final_score(
    goal: str,
    retention: float,
    positive: float,
    paid: float,
    platform: float,
    logic: float,
    character: float,
    hook: float,
    emotional: float,
    disagreement: float,
) -> float:
    if goal == "paid_conversion":
        score = 0.30 * paid + 0.20 * hook + 0.15 * emotional + 0.15 * retention + 0.10 * platform + 0.10 * character
    elif goal == "retention":
        score = 0.30 * retention + 0.20 * emotional + 0.15 * hook + 0.15 * logic + 0.10 * platform + 0.10 * positive
    elif goal == "platform_recommendation":
        score = 0.30 * platform + 0.25 * retention + 0.15 * positive + 0.15 * paid + 0.15 * hook
    else:
        score = 0.42 * positive + 0.22 * emotional + 0.16 * logic + 0.10 * retention + 0.06 * character + 0.04 * hook
    return max(0.0, min(0.98, score - disagreement))


def _avg(values: list[float]) -> float:
    return sum(values) / max(1, len(values))
