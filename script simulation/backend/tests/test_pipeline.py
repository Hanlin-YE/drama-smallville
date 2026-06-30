"""统计拟合管线首批测试：sampler → compressor → validator。

这三个是项目里最该测的深模块——接口小、实现大、杠杆高。
"""

from __future__ import annotations

import sys
import os

# 确保能 import backend 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from schemas.audience_distribution import AudienceDistributionConfig
from tests.factories import make_test_world, make_test_draft, make_test_persona

from population.sampler import sample_audience_population
from population.compressor import compress_population
from population.validator import validate_population_fit


# ── Sampler 测试 ──────────────────────────────────────────────────────────────

def _make_config() -> AudienceDistributionConfig:
    return AudienceDistributionConfig(
        distribution_id="test_dist",
        name="测试分布",
        source="test",
        platform_type="douyin_short_drama",
        confidence=0.7,
        categorical_distributions={
            "age_group": {"18_24": 0.35, "25_30": 0.30, "31_40": 0.20, "40_plus": 0.15},
            "city_tier": {"tier1": 0.25, "tier2": 0.35, "tier3": 0.25, "tier4": 0.15},
            "watch_frequency": {"daily": 0.20, "weekly": 0.45, "occasional": 0.35},
        },
        beta_distributions={
            "face_slapping_preference": (5.0, 3.0),
            "emotion_preference": (4.0, 4.0),
            "paid_propensity": (3.0, 5.0),
            "comment_propensity": (3.0, 4.0),
            "share_propensity": (2.0, 5.0),
            "quality_sensitivity": (4.0, 4.0),
        },
        bernoulli_distributions={"repeat_watch": 0.35},
        dirichlet_distributions={"genre_preferences": [3, 2, 2, 1, 1, 1]},
    )


class TestSampler:
    def test_returns_requested_size(self):
        config = _make_config()
        samples = sample_audience_population(config, size=100, seed=42)
        assert len(samples) == 100

    def test_seed_reproducibility(self):
        config = _make_config()
        s1 = sample_audience_population(config, size=50, seed=42)
        s2 = sample_audience_population(config, size=50, seed=42)
        assert s1[0].sample_id == s2[0].sample_id
        assert s1[0].behavior_propensities == s2[0].behavior_propensities

    def test_different_seeds_different_samples(self):
        config = _make_config()
        s1 = sample_audience_population(config, size=50, seed=42)
        s2 = sample_audience_population(config, size=50, seed=99)
        assert s1[0].behavior_propensities != s2[0].behavior_propensities

    def test_genre_preferences_sum_to_one(self):
        config = _make_config()
        samples = sample_audience_population(config, size=10, seed=42)
        for s in samples:
            total = sum(s.genre_preferences.values())
            assert abs(total - 1.0) < 0.01, f"genre_preferences sum={total}"

    def test_content_needs_populated(self):
        config = _make_config()
        samples = sample_audience_population(config, size=5, seed=42)
        for s in samples:
            assert "face_slapping_satisfaction" in s.content_needs
            assert "emotional_release" in s.content_needs

    def test_repeat_watch_is_bool(self):
        config = _make_config()
        samples = sample_audience_population(config, size=20, seed=42)
        for s in samples:
            assert isinstance(s.repeat_watch, bool)


# ── Compressor 测试 ───────────────────────────────────────────────────────────

class TestCompressor:
    def test_returns_at_most_max_agents(self):
        config = _make_config()
        samples = sample_audience_population(config, size=500, seed=42)
        agents = compress_population(samples, max_agents=6)
        assert len(agents) <= 6

    def test_segment_weights_sum_to_approx_one(self):
        config = _make_config()
        samples = sample_audience_population(config, size=500, seed=42)
        agents = compress_population(samples, max_agents=6)
        total = sum(a.segment_weight for a in agents)
        assert 0.95 <= total <= 1.05, f"weights sum={total}"

    def test_anchor_coverage_includes_paid_unlock(self):
        """_ensure_anchor_coverage 必须保证 paid_unlock 存在。"""
        from population.compressor import _base_archetype
        config = _make_config()
        samples = sample_audience_population(config, size=500, seed=42)
        agents = compress_population(samples, max_agents=6)
        archetypes = [_base_archetype(a.archetype) for a in agents]
        assert "paid_unlock" in archetypes, f"paid_unlock missing: {archetypes}"

    def test_each_agent_has_evidence(self):
        config = _make_config()
        samples = sample_audience_population(config, size=500, seed=42)
        agents = compress_population(samples, max_agents=6)
        for a in agents:
            assert len(a.evidence) >= 1
            assert a.evidence[0].source_type == "industry_report"

    def test_fallback_without_sklearn(self):
        """sklearn 不可用时降级到规则桶分配。"""
        config = _make_config()
        samples = sample_audience_population(config, size=100, seed=42)
        # 直接调 _assign_archetype 路径（sklearn 存在时也测规则路径）
        from population.compressor import _assign_archetype
        archetype = _assign_archetype(samples[0], 6)
        assert archetype in {"shuangwen_chaser", "emotion_immersive", "paid_unlock",
                             "tucao_spread", "quality_keeper", "platform_feed"}


# ── Validator 测试 ────────────────────────────────────────────────────────────

class TestValidator:
    def test_returns_population_fit_report(self):
        config = _make_config()
        samples = sample_audience_population(config, size=500, seed=42)
        agents = compress_population(samples, max_agents=6)
        report = validate_population_fit(config, samples, agents)
        assert report.distribution_error >= 0.0
        assert report.confidence_level in {"high", "medium", "low"}

    def test_accepted_when_error_low(self):
        config = _make_config()
        samples = sample_audience_population(config, size=500, seed=42)
        agents = compress_population(samples, max_agents=6)
        report = validate_population_fit(config, samples, agents)
        # 500 样本 + 6 agents 应该能通过
        assert report.accepted or report.distribution_error > 0.15

    def test_max_feature_error_populated(self):
        config = _make_config()
        samples = sample_audience_population(config, size=500, seed=42)
        agents = compress_population(samples, max_agents=6)
        report = validate_population_fit(config, samples, agents)
        assert len(report.max_feature_error) > 0
        for feature, error in report.max_feature_error.items():
            assert 0.0 <= error <= 2.0, f"{feature} error={error}"


# ── _judge_draft 拆分后测试 ───────────────────────────────────────────────────

class TestJudgeDraftSplit:
    def test_build_judge_text_contains_draft_and_world(self):
        from agents.audience_agents import _build_judge_text
        world = make_test_world()
        draft = make_test_draft()
        text = _build_judge_text(world, draft)
        assert "反杀局" in text
        assert "养父" in text

    def test_score_keywords_returns_signals(self):
        from agents.audience_agents import _score_keywords
        persona = make_test_persona()
        signals = _score_keywords("反杀 打脸 证据 拖沓", persona)
        assert signals["match"] == 3  # 反杀+打脸+证据
        assert signals["mismatch"] == 1  # 拖沓
        assert signals["hook"] >= 1  # 证据

    def test_apply_goal_boost_clamps_to_098(self):
        from agents.audience_agents import _apply_goal_boost
        signals = {"match": 5, "mismatch": 0, "hook": 3, "emotion": 2, "platform_boost": 0.0}
        scores = _apply_goal_boost(signals, "paid_conversion", make_test_draft(), "douyin_short_drama", "反杀 证据 真相")
        for key in ["continue_watch", "positive", "pay", "comment", "share"]:
            assert 0.0 <= scores[key] <= 0.98
        assert 0.0 <= scores["dropoff"] <= 0.98

    def test_generate_risks_when_mismatch(self):
        from agents.audience_agents import _generate_risks_triggers
        world = make_test_world()
        persona = make_test_persona(dislikes=["憋屈", "拖沓"])
        signals = {"match": 0, "mismatch": 1, "hook": 0, "emotion": 0, "platform_boost": 0.0}
        triggers, risks = _generate_risks_triggers("拖沓的剧情", persona, signals, world)
        assert any("反感" in r for r in risks)

    def test_judge_draft_end_to_end(self):
        from agents.audience_agents import _judge_draft
        world = make_test_world()
        draft = make_test_draft()
        persona = make_test_persona()
        j = _judge_draft(world, draft, persona, "round_1")
        assert 0.0 <= j.continue_watch <= 0.98
        assert 0.0 <= j.pay <= 0.98
        assert len(j.trigger_points) >= 1
        assert len(j.risk_points) >= 1
