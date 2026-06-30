from __future__ import annotations

import os
from collections import Counter, defaultdict

from schemas.evidence import PersonaEvidence
from schemas.population import RepresentativeAgentProfile, SampledAudience

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")


ARCHETYPES = [
    "shuangwen_chaser",
    "emotion_immersive",
    "paid_unlock",
    "tucao_spread",
    "quality_keeper",
    "platform_feed",
]


def compress_population(
    samples: list[SampledAudience],
    max_agents: int = 6,
    source_name: str = "audience_research",
    source_confidence: float = 0.6,
) -> list[RepresentativeAgentProfile]:
    kmeans_result = _compress_with_kmeans(samples, max_agents, source_name, source_confidence)
    if kmeans_result:
        return _ensure_anchor_coverage(kmeans_result, samples, max_agents, source_name, source_confidence)

    buckets: dict[str, list[SampledAudience]] = defaultdict(list)
    for sample in samples:
        buckets[_assign_archetype(sample, max_agents)].append(sample)

    total = max(1, len(samples))
    agents: list[RepresentativeAgentProfile] = []
    for archetype, items in sorted(buckets.items(), key=lambda pair: len(pair[1]), reverse=True):
        if not items:
            continue
        centroid = _centroid_features(items)
        agents.append(
            RepresentativeAgentProfile(
                agent_id=archetype,
                name=_name_for_archetype(archetype),
                archetype=archetype,
                cluster_size=len(items),
                segment_weight=round(len(items) / total, 4),
                centroid_features=centroid,
                categorical_summary=_categorical_summary(items),
                content_needs=_avg_dict([item.content_needs for item in items]),
                behavior_thresholds=_thresholds_from_centroid(centroid),
                evidence=[
                    PersonaEvidence(
                        source_type="industry_report",
                        source_name=source_name,
                        sample_size=len(items),
                        observed_metric=centroid,
                        confidence=source_confidence,
                    )
                ],
                confidence=source_confidence,
            )
        )
    return agents[:max_agents]


def _ensure_anchor_coverage(
    agents: list[RepresentativeAgentProfile],
    samples: list[SampledAudience],
    max_agents: int,
    source_name: str,
    source_confidence: float,
) -> list[RepresentativeAgentProfile]:
    required = ["paid_unlock", "platform_feed"]
    covered = {_base_archetype(agent.archetype) for agent in agents}
    result = list(agents)
    for archetype in required:
        if archetype in covered:
            continue
        replacement = _build_anchor_agent(archetype, samples, source_name, source_confidence)
        if not replacement:
            continue
        if len(result) >= max_agents:
            # Replace the smallest duplicate archetype to keep count stable.
            duplicate_index = _smallest_duplicate_index(result)
            if duplicate_index is not None:
                result[duplicate_index] = replacement
            else:
                result[-1] = replacement
        else:
            result.append(replacement)
        covered.add(archetype)
    total = sum(agent.segment_weight for agent in result) or 1.0
    normalized = [
        agent.model_copy(update={"segment_weight": round(agent.segment_weight / total, 4)})
        for agent in result
    ]
    return sorted(normalized, key=lambda item: item.segment_weight, reverse=True)


def _build_anchor_agent(
    archetype: str,
    samples: list[SampledAudience],
    source_name: str,
    source_confidence: float,
) -> RepresentativeAgentProfile | None:
    if not samples:
        return None
    if archetype == "paid_unlock":
        items = sorted(samples, key=lambda s: s.behavior_propensities.get("paid_propensity", 0), reverse=True)
    else:
        items = sorted(samples, key=_platform_signal, reverse=True)
    anchor_items = items[: max(20, len(samples) // 8)]
    centroid = _centroid_features(anchor_items)
    return RepresentativeAgentProfile(
        agent_id=archetype,
        name=_name_for_archetype(archetype),
        archetype=archetype,
        cluster_size=len(anchor_items),
        segment_weight=round(len(anchor_items) / len(samples), 4),
        centroid_features=centroid,
        categorical_summary=_categorical_summary(anchor_items),
        content_needs=_avg_dict([item.content_needs for item in anchor_items]),
        behavior_thresholds=_thresholds_from_centroid(centroid),
        evidence=[
            PersonaEvidence(
                source_type="industry_report",
                source_name=source_name,
                sample_size=len(anchor_items),
                observed_metric=centroid,
                confidence=source_confidence,
                note=f"Anchor representative for {archetype}",
            )
        ],
        confidence=source_confidence,
    )


def _smallest_duplicate_index(agents: list[RepresentativeAgentProfile]) -> int | None:
    counts: dict[str, int] = {}
    for agent in agents:
        counts[_base_archetype(agent.archetype)] = counts.get(_base_archetype(agent.archetype), 0) + 1
    duplicate_indices = [
        index
        for index, agent in enumerate(agents)
        if counts.get(_base_archetype(agent.archetype), 0) > 1
    ]
    if not duplicate_indices:
        return None
    return min(duplicate_indices, key=lambda index: agents[index].segment_weight)


def _base_archetype(archetype: str) -> str:
    return archetype.rsplit("_", 1)[0] if archetype.rsplit("_", 1)[-1].isdigit() else archetype


def _compress_with_kmeans(
    samples: list[SampledAudience],
    max_agents: int,
    source_name: str,
    source_confidence: float,
) -> list[RepresentativeAgentProfile] | None:
    try:
        import numpy as np
        from sklearn.cluster import KMeans
    except Exception:
        return None
    if len(samples) < max_agents:
        return None

    feature_names = _feature_names(samples)
    matrix = np.array([_feature_vector(sample, feature_names) for sample in samples], dtype=float)
    model = KMeans(n_clusters=max_agents, random_state=42, n_init=10)
    labels = model.fit_predict(matrix)

    agents: list[RepresentativeAgentProfile] = []
    for cluster_index in range(max_agents):
        items = [sample for sample, label in zip(samples, labels) if label == cluster_index]
        if not items:
            continue
        centroid = _centroid_features(items)
        archetype = _archetype_from_centroid(centroid, cluster_index)
        agents.append(
            RepresentativeAgentProfile(
                agent_id=archetype,
                name=_name_for_archetype(archetype),
                archetype=archetype,
                cluster_size=len(items),
                segment_weight=round(len(items) / len(samples), 4),
                centroid_features=centroid,
                categorical_summary=_categorical_summary(items),
                content_needs=_avg_dict([item.content_needs for item in items]),
                behavior_thresholds=_thresholds_from_centroid(centroid),
                evidence=[
                    PersonaEvidence(
                        source_type="industry_report",
                        source_name=source_name,
                        sample_size=len(items),
                        observed_metric=centroid,
                        confidence=source_confidence,
                        note="KMeans compressed representative agent",
                    )
                ],
                confidence=source_confidence,
            )
        )
    return sorted(agents, key=lambda item: item.segment_weight, reverse=True)


def _feature_names(samples: list[SampledAudience]) -> list[str]:
    keys = sorted(
        {
            key
            for sample in samples
            for key in list(sample.behavior_propensities) + list(sample.genre_preferences) + list(sample.content_needs)
        }
    )
    return keys + ["repeat_watch"]


def _feature_vector(sample: SampledAudience, feature_names: list[str]) -> list[float]:
    values = sample.behavior_propensities | sample.genre_preferences | sample.content_needs
    return [
        1.0 if name == "repeat_watch" and sample.repeat_watch else 0.0 if name == "repeat_watch" else values.get(name, 0.0)
        for name in feature_names
    ]


def _archetype_from_centroid(centroid: dict[str, float], index: int) -> str:
    candidates = {
        "shuangwen_chaser": centroid.get("face_slapping_preference", 0.0),
        "emotion_immersive": centroid.get("emotion_preference", 0.0),
        "paid_unlock": centroid.get("paid_propensity", 0.0),
        "tucao_spread": (centroid.get("comment_propensity", 0.0) + centroid.get("share_propensity", 0.0)) / 2,
        "quality_keeper": centroid.get("quality_sensitivity", 0.0),
        "platform_feed": (
            centroid.get("paid_propensity", 0.0)
            + centroid.get("comment_propensity", 0.0)
            + centroid.get("share_propensity", 0.0)
        )
        / 3,
    }
    base = max(candidates, key=candidates.get)
    return f"{base}_{index + 1}"


def _assign_archetype(sample: SampledAudience, max_agents: int) -> str:
    b = sample.behavior_propensities
    if max_agents <= 4:
        candidates = {
            "shuangwen_chaser": b.get("face_slapping_preference", 0),
            "emotion_immersive": b.get("emotion_preference", 0),
            "paid_unlock": b.get("paid_propensity", 0),
            "platform_feed": (b.get("comment_propensity", 0) + b.get("share_propensity", 0)) / 2,
        }
    else:
        candidates = {
            "shuangwen_chaser": b.get("face_slapping_preference", 0),
            "emotion_immersive": b.get("emotion_preference", 0),
            "paid_unlock": b.get("paid_propensity", 0),
            "tucao_spread": (b.get("comment_propensity", 0) + b.get("share_propensity", 0)) / 2,
            "quality_keeper": b.get("quality_sensitivity", 0),
            "platform_feed": _platform_signal(sample),
        }
    return max(candidates, key=candidates.get)


def _platform_signal(sample: SampledAudience) -> float:
    b = sample.behavior_propensities
    return (
        b.get("paid_propensity", 0) * 0.25
        + b.get("comment_propensity", 0) * 0.25
        + b.get("share_propensity", 0) * 0.25
        + (1.0 if sample.repeat_watch else 0.0) * 0.25
    )


def _centroid_features(items: list[SampledAudience]) -> dict[str, float]:
    return _avg_dict([item.behavior_propensities | item.genre_preferences for item in items])


def _avg_dict(dicts: list[dict[str, float]]) -> dict[str, float]:
    keys = sorted({key for data in dicts for key in data})
    return {
        key: round(sum(data.get(key, 0.0) for data in dicts) / max(1, len(dicts)), 4)
        for key in keys
    }


def _categorical_summary(items: list[SampledAudience]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for attr in ["age_group", "city_tier", "watch_frequency"]:
        values = [getattr(item, attr) for item in items if getattr(item, attr) is not None]
        counter = Counter(values)
        total = max(1, len(values))
        result[attr] = {key: round(value / total, 4) for key, value in counter.items()}
    result["repeat_watch"] = {
        "true": round(sum(1 for item in items if item.repeat_watch) / max(1, len(items)), 4)
    }
    return result


def _thresholds_from_centroid(centroid: dict[str, float]) -> dict[str, float]:
    paid = centroid.get("paid_propensity", 0.4)
    comment = centroid.get("comment_propensity", 0.3)
    quality = centroid.get("quality_sensitivity", 0.4)
    return {
        "pay": round(8.0 - paid * 3.0, 3),
        "comment": round(7.5 - comment * 3.0, 3),
        "dropoff": round(6.2 + quality * 1.6, 3),
    }


def _name_for_archetype(archetype: str) -> str:
    base = _base_archetype(archetype)
    return {
        "shuangwen_chaser": "爽点追更型",
        "emotion_immersive": "情感代入型",
        "paid_unlock": "付费解锁型",
        "tucao_spread": "吐槽传播型",
        "quality_keeper": "品质口碑型",
        "platform_feed": "平台推流 Agent",
    }.get(base, archetype)
