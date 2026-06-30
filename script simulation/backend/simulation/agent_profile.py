from __future__ import annotations

from dataclasses import dataclass, field

from schemas.population import RepresentativeAgentProfile


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    name: str
    segment_weight: float
    likes: list[str]
    dislikes: list[str]
    thresholds: dict[str, float]
    influence_power: float = 0.5
    susceptibility: float = 0.5
    speaking_style: str = ""


P0_MARKET_AGENTS: list[AgentProfile] = [
    AgentProfile(
        agent_id="audience_shuangwen",
        name="爽点追更型观众",
        segment_weight=0.28,
        likes=["反杀", "打脸", "证据", "主动", "强冲突"],
        dislikes=["憋屈", "拖沓", "过早和解"],
        thresholds={"pay": 7.0, "dropoff": 7.2},
        influence_power=0.55,
        susceptibility=0.45,
        speaking_style="直接、看重爽点兑现",
    ),
    AgentProfile(
        agent_id="audience_emotion",
        name="情感代入型观众",
        segment_weight=0.24,
        likes=["拉扯", "误会", "守护", "愧疚", "破防"],
        dislikes=["情感突兀", "人物冷漠", "动机薄弱"],
        thresholds={"pay": 6.8, "dropoff": 7.0},
        influence_power=0.45,
        susceptibility=0.65,
        speaking_style="关注情绪合理性",
    ),
    AgentProfile(
        agent_id="audience_paid_unlock",
        name="付费解锁型观众",
        segment_weight=0.30,
        likes=["付费点", "身份", "真相", "证据", "下一集必须看"],
        dislikes=["钩子弱", "提前揭晓", "兑现不足"],
        thresholds={"pay": 6.5, "dropoff": 7.4},
        influence_power=0.60,
        susceptibility=0.50,
        speaking_style="对卡点敏感",
    ),
    AgentProfile(
        agent_id="platform_distribution",
        name="平台推流 Agent",
        segment_weight=0.18,
        likes=["完读", "评论", "分享", "付费", "强标签"],
        dislikes=["标签不清", "开头慢", "疲劳"],
        thresholds={"pay": 7.0, "dropoff": 7.0},
        influence_power=0.80,
        susceptibility=0.20,
        speaking_style="运营和推荐视角",
    ),
]


def from_representative_agents(representatives: list[RepresentativeAgentProfile]) -> list[AgentProfile]:
    profiles: list[AgentProfile] = []
    for rep in representatives:
        centroid = rep.centroid_features
        profiles.append(
            AgentProfile(
                agent_id=rep.agent_id,
                name=rep.name,
                segment_weight=rep.segment_weight,
                likes=_likes_for_rep(rep),
                dislikes=_dislikes_for_rep(rep),
                thresholds={
                    "pay": rep.behavior_thresholds.get("pay", 7.0),
                    "dropoff": rep.behavior_thresholds.get("dropoff", 7.2),
                },
                influence_power=_clamp(centroid.get("share_propensity", 0.4) + centroid.get("comment_propensity", 0.3)),
                susceptibility=_clamp(0.35 + centroid.get("emotion_preference", 0.4) * 0.5),
                speaking_style=rep.name,
            )
        )
    return profiles or P0_MARKET_AGENTS


def _likes_for_rep(rep: RepresentativeAgentProfile) -> list[str]:
    archetype = rep.archetype
    if archetype == "paid_unlock":
        return ["付费点", "身份", "真相", "证据", "下一集必须看"]
    if archetype == "emotion_immersive":
        return ["拉扯", "误会", "守护", "愧疚", "破防"]
    if archetype == "tucao_spread":
        return ["争议", "吐槽", "反转", "名场面", "评论"]
    if archetype == "quality_keeper":
        return ["逻辑", "人设", "伏笔", "合理", "长期口碑"]
    if archetype == "platform_feed":
        return ["完读", "评论", "分享", "付费", "强标签"]
    return ["反杀", "打脸", "证据", "主动", "强冲突"]


def _dislikes_for_rep(rep: RepresentativeAgentProfile) -> list[str]:
    archetype = rep.archetype
    if archetype == "quality_keeper":
        return ["逻辑硬伤", "人物崩坏", "套路感"]
    if archetype == "platform_feed":
        return ["标签不清", "开头慢", "疲劳"]
    if archetype == "paid_unlock":
        return ["钩子弱", "提前揭晓", "兑现不足"]
    return ["憋屈", "拖沓", "过早和解"]


def _clamp(value: float) -> float:
    return max(0.05, min(0.95, value))
