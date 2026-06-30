"""LLM Gateway — ScriptMind 工具层适配器。

ScriptMind 提供 LLM 驱动的 /api/plan、/api/generate、/api/extract-features
端点（见 ADR-0001）。本类把这些端点适配为剧组 Role 可调用的方法，
不自建 LLM Key。请求参数由 Role 根据用户输入动态构造，不写死。
"""

from __future__ import annotations

import logging

from llm.script_mind_client import (
    GeneratedContent,
    PlanResponse,
    ScriptMindClient,
    SimulationResult,
    get_client,
)
from config.settings import settings
from schemas.draft import CandidateDraft
from schemas.judgment import AudienceJudgment

logger = logging.getLogger(__name__)


class LLMGateway:
    """Central gateway for all LLM and simulation calls.

    When ``settings.use_scriptmind`` is True, delegates to ScriptMind REST API.
    Falls back to mock/deterministic behavior on any failure.
    """

    def __init__(
        self,
        model_id: str = "mock",
        client: ScriptMindClient | None = None,
    ) -> None:
        self.model_id = model_id
        self._client = client or get_client()
        self._enabled = settings.use_scriptmind

    # ── A2 策划 Agent: generate candidate drafts ─────────────────────────

    def generate_candidate_drafts(
        self,
        genre: str,
        protagonist_setting: str,
        platform: str,
        additional_notes: str = "",
    ) -> PlanResponse | None:
        """Call ScriptMind /api/plan to generate 3 plot drafts."""
        if not self._enabled:
            logger.info("ScriptMind disabled, skipping plan call")
            return None
        return self._client.plan(
            genre=genre,
            protagonist_setting=protagonist_setting,
            platform=platform,
            additional_notes=additional_notes,
        )

    def map_plan_to_candidate_drafts(
        self,
        plan_response: PlanResponse,
        author_goal: str = "paid_conversion",
    ) -> list[CandidateDraft]:
        """Map ScriptMind draft responses to Drama Smallville CandidateDraft schema."""
        goal_reader_action: dict[str, str] = {
            "retention": "continue_reading",
            "positive_review": "give_positive_review",
            "paid_conversion": "pay_to_unlock",
            "platform_recommendation": "share",
        }
        default_action = goal_reader_action.get(author_goal, "continue_reading")

        candidates: list[CandidateDraft] = []
        for i, sd in enumerate(plan_response.drafts):
            draft_id = sd.id or f"draft_scriptmind_{i}"
            beats = [act.get("events", "") for act in sd.acts if act.get("events")]
            hook_text = sd.hooks[0] if sd.hooks else sd.synopsis[:50]
            candidates.append(
                CandidateDraft(
                    draft_id=draft_id,
                    title=sd.title,
                    synopsis=sd.synopsis,
                    key_beats=beats or [sd.synopsis[:80]],
                    intended_hook=hook_text,
                    intended_emotion=sd.dominant_emotion or "好奇",
                    expected_reader_action=default_action,
                    author_note=f"ScriptMind A2 生成 · 风格: {sd.style}",
                )
            )
        return candidates

    # ── ABM 模拟: run audience simulation ────────────────────────────────

    def run_abm_simulation(
        self,
        agent_config_id: str,
        text: str,
        title: str = "",
    ) -> SimulationResult | None:
        """Run ABM simulation against an existing ScriptMind agent config."""
        if not self._enabled:
            logger.info("ScriptMind disabled, skipping simulation")
            return None
        return self._client.simulate(agent_config_id, text, title)

    def map_simulation_to_judgments(
        self,
        result: SimulationResult,
        draft_ids: list[str],
    ) -> list[AudienceJudgment]:
        """Map a single ScriptMind SimulationResult to multiple AudienceJudgments,
        one per agent archetype, estimated from the simulation output.
        """
        judgments: list[AudienceJudgment] = []
        archetypes = [
            ("audience_shuangwen", "heavy_user"),
            ("audience_emotion", "emotional_fan"),
            ("audience_paid_unlock", "reward_seeker"),
            ("platform_distribution", "social_spreader"),
        ]
        s = result.scores
        grade_mult = {"S+": 1.2, "S": 1.1, "A": 1.0, "B": 0.85, "C": 0.65}
        mult = grade_mult.get(result.grade, 1.0)

        for draft_id in draft_ids:
            for agent_id, _archetype in archetypes:
                cw = min(0.98, (s.overall * 0.7 + s.emotion_resonance * 0.3) * mult + 0.05)
                pr = min(0.98, (s.emotion_resonance * 0.6 + s.overall * 0.4) * mult)
                pay = min(0.98, (s.viral_potential * 0.5 + s.overall * 0.5) * mult + 0.02)
                drop = max(0.05, 0.45 - s.overall * 0.3 + (1 - s.emotion_resonance) * 0.25)
                share = min(0.98, s.viral_potential * mult * 0.8)
                comment = min(0.98, s.opinion_convergence * mult)

                triggers: list[str] = []
                risks: list[str] = []
                for ev in result.emergence_events:
                    if ev.type in ("viral_outbreak", "emotional_resonance_storm"):
                        triggers.append(f"Tick {ev.tick}: {ev.description}")
                    if ev.type in ("churn_wave", "opinion_polarization"):
                        risks.append(f"Tick {ev.tick}: {ev.description}")

                judgments.append(
                    AudienceJudgment(
                        agent_id=agent_id,
                        draft_id=draft_id,
                        round_id="round_1",
                        continue_watch=round(cw, 3),
                        positive_review=round(pr, 3),
                        pay=round(pay, 3),
                        comment=round(comment, 3),
                        share=round(share, 3),
                        dropoff=round(drop, 3),
                        platform_recommendation=round(s.viral_potential * mult, 3),
                        trigger_points=triggers or [f"情绪共鸣 {s.emotion_resonance:.2f}"],
                        risk_points=risks or [f"弃坑风险 {drop:.2f}"],
                        confidence=0.72,
                    )
                )
        return judgments

    # ── Content generation ───────────────────────────────────────────────

    def generate_content(
        self,
        result: dict[str, Any] | None = None,
        draft: dict[str, Any] | None = None,
    ) -> GeneratedContent | None:
        """Generate titles, hooks, suggestions via A5 文案生成 Agent."""
        if not self._enabled:
            return None
        return self._client.generate(result, draft)

    # ── Feature extraction ───────────────────────────────────────────────

    def extract_content_features(self, text: str) -> dict[str, float]:
        """Extract semantic features from content text."""
        if not self._enabled:
            return {}
        features = self._client.extract_features(text)
        if features:
            return {
                "hook_density": features.hook_density,
                "emotion_volatility": features.emotion_volatility,
                "peak_intensity": features.peak_intensity,
                "base_shareability": features.base_shareability,
                "controversy_score": features.controversy_score,
            }
        return {}

