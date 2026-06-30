from __future__ import annotations

from schemas.population import AgentProfileSet
from population.compressor import compress_population
from population.distribution_loader import load_distribution
from population.sampler import sample_audience_population
from population.validator import validate_population_fit


def build_agent_profile_set(
    platform_type: str,
    business_goal: str,
    distribution_id: str | None = None,
    population_size: int = 500,
    max_agents: int = 6,
    seed: int = 42,
) -> AgentProfileSet:
    config = load_distribution(distribution_id, platform_type)
    samples = sample_audience_population(config, size=population_size, seed=seed)
    agents = compress_population(
        samples,
        max_agents=max_agents,
        source_name=config.source,
        source_confidence=config.confidence,
    )
    fit = validate_population_fit(config, samples, agents)
    return AgentProfileSet(
        profile_set_id=f"{config.distribution_id}_{max_agents}_{seed}",
        platform_type=platform_type,
        business_goal=business_goal,
        representative_agents=agents,
        distribution_id=config.distribution_id,
        population_fit=fit,
    )

