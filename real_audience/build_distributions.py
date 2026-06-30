from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "platform_catalog.json"
NORMALIZED_PATH = ROOT / "normalized" / "audience_samples.jsonl"
PROFILES_DIR = ROOT / "profiles"
DEFAULT_OUTPUT = PROFILES_DIR / "audience_distributions.json"
PERSONA_CARDS = PROFILES_DIR / "persona_seed_cards.md"

GENRE_KEYS = ["revenge", "romance", "suspense", "comedy", "family", "workplace"]
BEHAVIOR_KEYS = [
    "paid_propensity",
    "comment_propensity",
    "share_propensity",
    "face_slapping_preference",
    "emotion_preference",
    "quality_sensitivity",
]

SHORT_DRAMA_PLATFORMS = {
    "xidian_short_drama",
    "hongguo_short_drama",
    "douyin_short_drama",
    "kuaishou_short_drama",
}
WEB_NOVEL_PLATFORMS = {
    "fanqie_web_novel",
    "jinjiang",
    "qimao_web_novel",
    "qidian",
}

PLATFORM_OVERRIDES = {
    "xidian_short_drama": {"paid_propensity": 0.48, "face_slapping_preference": 0.66, "emotion_preference": 0.56},
    "hongguo_short_drama": {"paid_propensity": 0.36, "comment_propensity": 0.42, "share_propensity": 0.38},
    "douyin_short_drama": {"comment_propensity": 0.58, "share_propensity": 0.54, "face_slapping_preference": 0.62},
    "kuaishou_short_drama": {"comment_propensity": 0.53, "share_propensity": 0.47, "emotion_preference": 0.58},
    "fanqie_web_novel": {"paid_propensity": 0.34, "face_slapping_preference": 0.56, "quality_sensitivity": 0.46},
    "jinjiang": {"emotion_preference": 0.68, "quality_sensitivity": 0.6, "paid_propensity": 0.32},
    "qimao_web_novel": {"paid_propensity": 0.28, "face_slapping_preference": 0.52, "comment_propensity": 0.34},
    "qidian": {"paid_propensity": 0.46, "quality_sensitivity": 0.62, "comment_propensity": 0.38},
}


def main() -> None:
    args = _parse_args()
    distributions = build_distributions(args.input, args.catalog)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(distributions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PERSONA_CARDS.write_text(build_persona_cards(distributions), encoding="utf-8")
    print(f"Wrote {len(distributions)} platform distributions to {args.output}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build backend-loadable audience distributions from normalized samples.")
    parser.add_argument("--input", type=Path, default=NORMALIZED_PATH)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def build_distributions(normalized_path: Path = NORMALIZED_PATH, catalog_path: Path = CATALOG_PATH) -> dict[str, dict[str, Any]]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    grouped = group_samples(load_samples(normalized_path))
    distributions: dict[str, dict[str, Any]] = {}
    for platform in catalog.get("platforms", []):
        platform_type = platform["platform_type"]
        samples = grouped.get(platform_type, [])
        config = build_distribution_for_platform(platform, samples)
        distributions[config["distribution_id"]] = config
    return distributions


def load_samples(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    samples: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                samples.append(json.loads(line))
    return samples


def group_samples(samples: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sample in samples:
        grouped[str(sample.get("platform_type", "unknown"))].append(sample)
    return grouped


def build_distribution_for_platform(platform: dict[str, Any], samples: list[dict[str, Any]]) -> dict[str, Any]:
    platform_type = platform["platform_type"]
    family = platform.get("content_family", "web_novel")
    sample_count = len(samples)
    behavior_means = behavior_means_for(platform_type, family, samples)
    genre_values = genre_values_for(platform_type, family, samples)
    confidence = confidence_for(sample_count, platform.get("collection_status", "unknown"))
    source_notes = list(platform.get("source_notes", []))
    if sample_count == 0:
        source_notes.append("No normalized samples yet; distribution uses public-platform priors until collection is run.")
    else:
        source_notes.append(f"Built from {sample_count} public normalized samples.")
    return {
        "distribution_id": f"{platform_type}_public_seed_v1",
        "name": f"{platform.get('display_name', platform_type)} public audience seed",
        "source": "real_audience public app reviews/comments + platform priors",
        "source_notes": source_notes,
        "sample_size": sample_count,
        "platform_type": platform_type,
        "categorical_distributions": categorical_distributions(family),
        "bernoulli_distributions": {
            "repeat_watch": round(0.5 + behavior_means["face_slapping_preference"] * 0.18, 4)
        },
        "beta_distributions": {
            key: beta_from_mean(value, concentration_for(sample_count))
            for key, value in behavior_means.items()
        },
        "dirichlet_distributions": {
            "genre_preferences": genre_values
        },
        "platform_feed_weights": feed_weights_for(platform_type, family),
        "confidence": confidence,
    }


def behavior_means_for(platform_type: str, family: str, samples: list[dict[str, Any]]) -> dict[str, float]:
    base = base_behavior(family)
    base.update(PLATFORM_OVERRIDES.get(platform_type, {}))
    if not samples:
        return {key: round(base[key], 4) for key in BEHAVIOR_KEYS}
    sample_means = {
        key: mean([
            float(sample.get("behavior_signals", {}).get(key, base[key]))
            for sample in samples
        ])
        for key in BEHAVIOR_KEYS
    }
    sample_weight = min(0.65, 0.2 + math.log1p(len(samples)) / 10)
    return {
        key: round(base[key] * (1 - sample_weight) + sample_means[key] * sample_weight, 4)
        for key in BEHAVIOR_KEYS
    }


def genre_values_for(platform_type: str, family: str, samples: list[dict[str, Any]]) -> list[float]:
    base = base_genres(platform_type, family)
    if not samples:
        return base
    means = [
        mean([float(sample.get("genre_signals", {}).get(key, base[index])) for sample in samples])
        for index, key in enumerate(GENRE_KEYS)
    ]
    sample_weight = min(0.6, 0.2 + math.log1p(len(samples)) / 10)
    mixed = [base[index] * (1 - sample_weight) + means[index] * sample_weight for index in range(len(GENRE_KEYS))]
    total = sum(mixed) or 1.0
    return [round(max(0.05, value / total * 10), 4) for value in mixed]


def base_behavior(family: str) -> dict[str, float]:
    if family == "short_drama":
        return {
            "paid_propensity": 0.4,
            "comment_propensity": 0.4,
            "share_propensity": 0.34,
            "face_slapping_preference": 0.62,
            "emotion_preference": 0.56,
            "quality_sensitivity": 0.38,
        }
    return {
        "paid_propensity": 0.34,
        "comment_propensity": 0.32,
        "share_propensity": 0.24,
        "face_slapping_preference": 0.5,
        "emotion_preference": 0.52,
        "quality_sensitivity": 0.54,
    }


def base_genres(platform_type: str, family: str) -> list[float]:
    if platform_type == "jinjiang":
        return [1.2, 3.2, 1.2, 0.9, 1.2, 1.4]
    if platform_type == "qidian":
        return [2.0, 1.0, 2.4, 0.8, 1.0, 1.8]
    if family == "short_drama":
        return [2.5, 2.0, 1.3, 0.8, 1.7, 0.9]
    return [2.0, 2.0, 1.6, 0.8, 1.2, 1.4]


def categorical_distributions(family: str) -> dict[str, dict[str, float]]:
    if family == "short_drama":
        return {
            "watch_frequency": {"daily": 0.34, "weekly_multi": 0.42, "occasional": 0.24},
            "city_tier": {"tier_1_2": 0.32, "tier_3_lower": 0.68},
        }
    return {
        "age_group": {"gen_z": 0.28, "age_26_45": 0.48, "age_45_60": 0.16, "age_60_plus": 0.08},
        "watch_frequency": {"daily": 0.27, "weekly_multi": 0.43, "occasional": 0.30},
    }


def feed_weights_for(platform_type: str, family: str) -> dict[str, float]:
    if platform_type in {"douyin_short_drama", "kuaishou_short_drama"}:
        return {
            "retention": 0.28,
            "comment": 0.22,
            "share": 0.2,
            "paid_conversion": 0.14,
            "positive_review": 0.08,
            "platform_fit": 0.08,
            "dropoff_penalty": 0.24,
        }
    if family == "short_drama":
        return {
            "retention": 0.3,
            "paid_conversion": 0.22,
            "comment": 0.18,
            "share": 0.14,
            "positive_review": 0.08,
            "platform_fit": 0.08,
            "dropoff_penalty": 0.25,
        }
    return {
        "retention": 0.34,
        "positive_review": 0.2,
        "comment": 0.15,
        "paid_conversion": 0.15,
        "platform_fit": 0.16,
    }


def beta_from_mean(value: float, concentration: float) -> list[float]:
    clamped = max(0.02, min(0.98, value))
    alpha = round(clamped * concentration, 4)
    beta = round((1 - clamped) * concentration, 4)
    return [max(0.05, alpha), max(0.05, beta)]


def concentration_for(sample_count: int) -> float:
    return round(min(12.0, 5.0 + math.log1p(sample_count)), 4)


def confidence_for(sample_count: int, collection_status: str) -> float:
    if sample_count <= 0:
        return 0.42
    coverage_penalty = 0.05 if "requires" in collection_status else 0.0
    confidence = 0.5 + min(0.25, math.log1p(sample_count) / 12) - coverage_penalty
    return round(max(0.35, min(0.75, confidence)), 4)


def build_persona_cards(distributions: dict[str, dict[str, Any]]) -> str:
    lines = [
        "# Real Audience Persona Seed Cards",
        "",
        "These cards summarize aggregate public signals. They do not contain user identifiers or long verbatim comments.",
        "",
    ]
    for config in distributions.values():
        behaviors = {key: round(values[0] / max(0.01, values[0] + values[1]), 3) for key, values in config["beta_distributions"].items()}
        genres = dict(zip(GENRE_KEYS, config["dirichlet_distributions"]["genre_preferences"]))
        top_behavior = sorted(behaviors.items(), key=lambda item: item[1], reverse=True)[:3]
        top_genres = sorted(genres.items(), key=lambda item: item[1], reverse=True)[:3]
        lines.extend([
            f"## {config['name']}",
            "",
            f"- `platform_type`: `{config['platform_type']}`",
            f"- `distribution_id`: `{config['distribution_id']}`",
            f"- sample size: {config.get('sample_size', 0)}, confidence: {config['confidence']}",
            f"- strongest behavior signals: {', '.join(f'{key}={value}' for key, value in top_behavior)}",
            f"- strongest genre signals: {', '.join(f'{key}={value}' for key, value in top_genres)}",
            "- representative seeds:爽点追更型, 情感代入型, 付费解锁型, 吐槽传播型, 品质口碑型, 平台推流型",
            "",
        ])
    return "\n".join(lines)


if __name__ == "__main__":
    main()

