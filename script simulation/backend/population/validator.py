from __future__ import annotations

from collections import Counter

from schemas.audience_distribution import AudienceDistributionConfig
from schemas.population import PopulationFitReport, RepresentativeAgentProfile, SampledAudience


def validate_population_fit(
    config: AudienceDistributionConfig,
    samples: list[SampledAudience],
    agents: list[RepresentativeAgentProfile],
) -> PopulationFitReport:
    target = _target_distributions(config)
    representative = _representative_distributions(agents)
    max_errors: dict[str, float] = {}
    total_error = 0.0
    count = 0
    for feature, target_dist in target.items():
        rep_dist = representative.get(feature, {})
        keys = set(target_dist) | set(rep_dist)
        error = sum(abs(target_dist.get(key, 0.0) - rep_dist.get(key, 0.0)) for key in keys)
        max_errors[feature] = round(error, 4)
        total_error += error
        count += 1
    distribution_error = round(total_error / max(1, count), 4)
    confidence = "high" if distribution_error <= 0.08 else "medium" if distribution_error <= 0.15 else "low"
    return PopulationFitReport(
        target_distribution=target,
        representative_distribution=representative,
        distribution_error=distribution_error,
        max_feature_error=max_errors,
        accepted=distribution_error <= 0.15,
        confidence_level=confidence,
    )


def _target_distributions(config: AudienceDistributionConfig) -> dict:
    target = dict(config.categorical_distributions)
    for key, value in config.bernoulli_distributions.items():
        target[key] = {"true": value, "false": round(1 - value, 4)}
    return target


def _representative_distributions(agents: list[RepresentativeAgentProfile]) -> dict:
    result: dict[str, dict[str, float]] = {}
    for agent in agents:
        weight = agent.segment_weight
        for feature, dist in agent.categorical_summary.items():
            result.setdefault(feature, {})
            for key, value in dist.items():
                result[feature][key] = result[feature].get(key, 0.0) + value * weight
    return {
        feature: {key: round(value, 4) for key, value in dist.items()}
        for feature, dist in result.items()
    }

