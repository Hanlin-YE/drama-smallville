from __future__ import annotations

import random
from math import gamma

from schemas.audience_distribution import AudienceDistributionConfig
from schemas.population import SampledAudience


GENRE_KEYS = ["revenge", "romance", "suspense", "comedy", "family", "workplace"]


def sample_audience_population(
    config: AudienceDistributionConfig,
    size: int = 500,
    seed: int = 42,
) -> list[SampledAudience]:
    rng = random.Random(seed)
    samples: list[SampledAudience] = []
    for index in range(size):
        categorical = {
            name: _sample_categorical(rng, dist)
            for name, dist in config.categorical_distributions.items()
        }
        behaviors = {
            name: rng.betavariate(alpha, beta)
            for name, (alpha, beta) in config.beta_distributions.items()
        }
        genre_values = _sample_dirichlet(
            rng,
            next(iter(config.dirichlet_distributions.values()), [1, 1, 1, 1, 1, 1]),
        )
        genre_preferences = {
            GENRE_KEYS[i]: round(value, 4)
            for i, value in enumerate(genre_values[: len(GENRE_KEYS)])
        }
        content_needs = _content_needs_from_behaviors(behaviors)
        samples.append(
            SampledAudience(
                sample_id=f"aud_{index:04d}",
                age_group=categorical.get("age_group"),
                city_tier=categorical.get("city_tier"),
                watch_frequency=categorical.get("watch_frequency", "occasional"),
                repeat_watch=_sample_bernoulli(rng, config.bernoulli_distributions.get("repeat_watch", 0.4)),
                platform_type=config.platform_type,
                genre_preferences=genre_preferences,
                behavior_propensities={k: round(v, 4) for k, v in behaviors.items()},
                content_needs=content_needs,
            )
        )
    return samples


def _sample_categorical(rng: random.Random, dist: dict[str, float]) -> str:
    roll = rng.random()
    acc = 0.0
    fallback = next(iter(dist))
    for key, value in dist.items():
        acc += value
        if roll <= acc:
            return key
    return fallback


def _sample_bernoulli(rng: random.Random, p: float) -> bool:
    return rng.random() < p


def _sample_dirichlet(rng: random.Random, alphas: list[float]) -> list[float]:
    # Gamma sampling is the standard construction for Dirichlet.
    draws = [rng.gammavariate(max(alpha, 0.001), 1.0) for alpha in alphas]
    total = sum(draws) or 1.0
    return [draw / total for draw in draws]


def _content_needs_from_behaviors(behaviors: dict[str, float]) -> dict[str, float]:
    return {
        "face_slapping_satisfaction": round(behaviors.get("face_slapping_preference", 0.5), 4),
        "emotional_release": round(behaviors.get("emotion_preference", 0.5), 4),
        "curiosity_resolution": round((behaviors.get("paid_propensity", 0.4) + behaviors.get("share_propensity", 0.2)) / 2, 4),
        "social_talk": round(behaviors.get("comment_propensity", 0.3), 4),
        "aesthetic_quality": round(behaviors.get("quality_sensitivity", 0.4), 4),
    }

