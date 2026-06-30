"""ScriptMind REST API client for Agent-Based Social Dynamics Simulation.

Wraps all ScriptMind API endpoints with typed request/response models and
graceful error handling that falls back to None on failure so callers can
degrade to mock/rule-based logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


# ── Response models ───────────────────────────────────────────────────────────

@dataclass
class ScriptDraft:
    """A single draft returned by /api/plan (A2 策划 Agent)."""
    id: str
    title: str
    style: str
    synopsis: str
    acts: list[dict[str, str]] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    dominant_emotion: str = ""


@dataclass
class PlanResponse:
    """Response from /api/plan."""
    drafts: list[ScriptDraft] = field(default_factory=list)


@dataclass
class SimulationScores:
    overall: float = 0.0
    viral_potential: float = 0.0
    emotion_resonance: float = 0.0
    opinion_convergence: float = 0.0


@dataclass
class SimulationPropagation:
    peak_viral_r: float = 0.0
    final_share_rate: str = "0%"
    final_churn_rate: str = "0%"
    break_circle_tick: int = 0


@dataclass
class SimulationEmotion:
    dominant_emotion: str = "neutral"
    peak_synchrony: float = 0.0
    resonance_duration: int = 0


@dataclass
class SimulationOpinion:
    polarization_index: float = 0.0
    convergence_index: float = 0.0
    kol_influence_score: float = 0.0


@dataclass
class EmergenceEvent:
    type: str = ""
    tick: int = 0
    magnitude: float = 0.0
    description: str = ""


@dataclass
class SimulationResult:
    simulation_id: str = ""
    agent_config_id: str = ""
    status: str = ""
    grade: str = ""
    scores: SimulationScores = field(default_factory=SimulationScores)
    propagation: SimulationPropagation = field(default_factory=SimulationPropagation)
    emotion: SimulationEmotion = field(default_factory=SimulationEmotion)
    opinion: SimulationOpinion = field(default_factory=SimulationOpinion)
    emergence_events: list[EmergenceEvent] = field(default_factory=list)
    content_title: str = ""


@dataclass
class FeatureExtraction:
    hook_density: float = 0.0
    emotion_volatility: float = 0.0
    peak_intensity: float = 0.0
    base_shareability: float = 0.0
    controversy_score: float = 0.0


@dataclass
class GeneratedContent:
    titles: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    platform_copy: dict[str, str] = field(default_factory=dict)


@dataclass
class AgentConfig:
    id: str = ""
    name: str = ""
    platform: str = "douyin"
    agent_count: int = 500
    kol_ratio: float = 0.05
    ticks: int = 100
    rewire_prob: float = 0.1


# ── Client ────────────────────────────────────────────────────────────────────

class ScriptMindClient:
    """HTTP client for ScriptMind Agent-Based Social Dynamics Simulation API."""

    def __init__(self) -> None:
        self._base = settings.scriptmind_base_url.rstrip("/")
        self._key = settings.scriptmind_api_key
        self._headers = {
            "X-API-Key": self._key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ── Agent config CRUD ─────────────────────────────────────────────────

    def create_agent_config(
        self,
        name: str,
        platform: str = "douyin",
        agent_count: int = 500,
        kol_ratio: float = 0.05,
        ticks: int = 100,
        rewire_prob: float = 0.1,
        audience_distribution: dict[str, float] | None = None,
    ) -> AgentConfig | None:
        """Create a persistent agent configuration for simulation."""
        default_dist = {
            "heavy_user": 0.12,
            "casual_reader": 0.25,
            "social_spreader": 0.12,
            "reward_seeker": 0.15,
            "skeptic": 0.08,
            "emotional_fan": 0.10,
            "trend_follower": 0.08,
            "critic": 0.04,
            "lurker": 0.04,
            "controversy_hunter": 0.02,
        }
        body = {
            "name": name,
            "platform": platform,
            "agentCount": agent_count,
            "kolRatio": kol_ratio,
            "ticks": ticks,
            "rewireProb": rewire_prob,
            "audienceDistribution": audience_distribution or default_dist,
        }
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(f"{self._base}/api/agents", json=body, headers=self._headers)
                if resp.status_code == 201:
                    data = resp.json()
                    return AgentConfig(
                        id=data["id"],
                        name=data["name"],
                        platform=data["platform"],
                        agent_count=data["agentCount"],
                        kol_ratio=data["kolRatio"],
                        ticks=data["ticks"],
                        rewire_prob=data["rewireProb"],
                    )
                logger.warning("ScriptMind create_agent_config failed: %s %s", resp.status_code, resp.text[:200])
                return None
        except Exception as exc:
            logger.warning("ScriptMind create_agent_config error: %s", exc)
            return None

    # ── Simulation ────────────────────────────────────────────────────────

    def simulate(self, agent_config_id: str, text: str, title: str = "") -> SimulationResult | None:
        """Run ABM simulation for given content against an existing agent config."""
        body = {"text": text, "title": title}
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    f"{self._base}/api/agents/{agent_config_id}/simulate",
                    json=body,
                    headers=self._headers,
                )
                if resp.status_code == 200:
                    return self._parse_simulation_result(resp.json())
                logger.warning("ScriptMind simulate failed: %s %s", resp.status_code, resp.text[:200])
                return None
        except Exception as exc:
            logger.warning("ScriptMind simulate error: %s", exc)
            return None

    def _parse_simulation_result(self, data: dict[str, Any]) -> SimulationResult:
        scores = data.get("scores", {})
        prop = data.get("propagation", {})
        emo = data.get("emotion", {})
        opi = data.get("opinion", {})
        content = data.get("content", {})
        return SimulationResult(
            simulation_id=data.get("simulationId", ""),
            agent_config_id=data.get("agentConfigId", ""),
            status=data.get("status", ""),
            grade=data.get("grade", ""),
            scores=SimulationScores(
                overall=scores.get("overall", 0.0),
                viral_potential=scores.get("viralPotential", 0.0),
                emotion_resonance=scores.get("emotionResonance", 0.0),
                opinion_convergence=scores.get("opinionConvergence", 0.0),
            ),
            propagation=SimulationPropagation(
                peak_viral_r=prop.get("peakViralR", 0.0),
                final_share_rate=prop.get("finalShareRate", "0%"),
                final_churn_rate=prop.get("finalChurnRate", "0%"),
                break_circle_tick=prop.get("breakCircleTick", 0),
            ),
            emotion=SimulationEmotion(
                dominant_emotion=emo.get("dominantEmotion", "neutral"),
                peak_synchrony=emo.get("peakSynchrony", 0.0),
                resonance_duration=emo.get("resonanceDuration", 0),
            ),
            opinion=SimulationOpinion(
                polarization_index=opi.get("polarizationIndex", 0.0),
                convergence_index=opi.get("convergenceIndex", 0.0),
                kol_influence_score=opi.get("kolInfluenceScore", 0.0),
            ),
            emergence_events=[
                EmergenceEvent(
                    type=ev.get("type", ""),
                    tick=ev.get("tick", 0),
                    magnitude=ev.get("magnitude", 0.0),
                    description=ev.get("description", ""),
                )
                for ev in data.get("emergenceEvents", [])
            ],
            content_title=content.get("title", ""),
        )

    # ── Feature extraction ────────────────────────────────────────────────

    def extract_features(self, text: str) -> FeatureExtraction | None:
        """Extract semantic features from content via LLM."""
        body = {"text": text[:3000]}
        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(f"{self._base}/api/extract-features", json=body, headers=self._headers)
                if resp.status_code == 200:
                    data = resp.json()
                    # 响应格式: {"success":true,"features":{...}}
                    feats = data.get("features", data)
                    return FeatureExtraction(
                        hook_density=feats.get("hookDensity", 0.0),
                        emotion_volatility=feats.get("emotionVolatility", 0.0),
                        peak_intensity=feats.get("peakIntensity", 0.0),
                        base_shareability=feats.get("baseShareability", 0.0),
                        controversy_score=feats.get("controversyScore", 0.0),
                    )
                logger.warning("ScriptMind extract_features failed: %s", resp.status_code)
                return None
        except Exception as exc:
            logger.warning("ScriptMind extract_features error: %s", exc)
            return None

    # ── Plan generation (A2 策划 Agent) ───────────────────────────────────

    def plan(
        self,
        genre: str,
        protagonist_setting: str,
        platform: str = "douyin",
        additional_notes: str = "",
    ) -> PlanResponse | None:
        """Generate 3 candidate drafts via the A2 planning agent.

        genre 必须是英文枚举（suspense/revenge/comedy/family 等），中文 genre
        会触发 ScriptMind 后端 500。调用方传中文时自动映射。
        """
        body = {
            "genre": _normalize_genre(genre),
            "protagonistSetting": protagonist_setting,
            "platform": platform,
            "additionalNotes": additional_notes,
        }
        try:
            with httpx.Client(timeout=90) as client:
                resp = client.post(f"{self._base}/api/plan", json=body, headers=self._headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return PlanResponse(
                        drafts=[
                            ScriptDraft(
                                id=d.get("id", f"plan_{i}"),
                                title=d.get("title", ""),
                                style=d.get("style", ""),
                                synopsis=d.get("synopsis", ""),
                                # ScriptMind 返回 outline/hookPoints/targetEmotion，
                                # 适配到 ScriptDraft 的 acts/hooks/dominant_emotion
                                acts=d.get("acts") or [{"outline": d.get("outline", "")}],
                                hooks=d.get("hooks") or d.get("hookPoints", []),
                                dominant_emotion=d.get("dominantEmotion") or d.get("targetEmotion", ""),
                            )
                            for i, d in enumerate(data.get("drafts", []))
                        ]
                    )
                logger.warning("ScriptMind plan failed: %s %s", resp.status_code, resp.text[:200])
                return None
        except Exception as exc:
            logger.warning("ScriptMind plan error: %s", exc)
            return None

    # ── Content generation (A5 文案生成 Agent) ────────────────────────────

    def generate(self, result: dict[str, Any] | None = None, draft: dict[str, Any] | None = None) -> GeneratedContent | None:
        """Generate titles, hooks, and suggestions via the A5 copywriter agent."""
        body: dict[str, Any] = {}
        if result:
            body["result"] = result
        if draft:
            body["draft"] = draft
        try:
            with httpx.Client(timeout=90) as client:
                resp = client.post(f"{self._base}/api/generate", json=body, headers=self._headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return GeneratedContent(
                        titles=data.get("titles", []),
                        hooks=data.get("hooks", []),
                        suggestions=data.get("suggestions", []),
                        platform_copy=data.get("platformCopy", {}),
                    )
                logger.warning("ScriptMind generate failed: %s", resp.status_code)
                return None
        except Exception as exc:
            logger.warning("ScriptMind generate error: %s", exc)
            return None


# ── Singleton ─────────────────────────────────────────────────────────────────

_client: ScriptMindClient | None = None


def get_client() -> ScriptMindClient:
    global _client
    if _client is None:
        _client = ScriptMindClient()
    return _client


# ── Genre 映射（ScriptMind /api/plan 要求英文枚举） ──────────────────────────

_GENRE_MAP: dict[str, str] = {
    "悬疑": "suspense", "推理": "suspense", "悬疑推理": "suspense",
    "复仇": "revenge", "爽文": "revenge", "复仇爽文": "revenge",
    "甜宠": "romance", "言情": "romance", "爱情": "romance", "甜虐": "romance",
    "搞笑": "comedy", "喜剧": "comedy",
    "家庭": "family", "家庭伦理": "family", "伦理": "family",
    "职场": "workplace", "都市": "workplace", "都市职场": "workplace",
    "古装": "period", "古风": "period", "历史": "period",
    "玄幻": "fantasy", "仙侠": "fantasy",
    "短剧": "suspense", "剧情测试": "suspense",  # 默认 fallback
}


def _normalize_genre(genre: str) -> str:
    """中文 genre → 英文枚举。已英文或未命中则原样返回。"""
    if not genre:
        return "suspense"  # 空值默认 suspense（已验证 200）
    genre = genre.strip()
    if genre.lower() in {"suspense", "revenge", "romance", "comedy", "family",
                         "workplace", "period", "fantasy"}:
        return genre.lower()
    return _GENRE_MAP.get(genre, "suspense")
