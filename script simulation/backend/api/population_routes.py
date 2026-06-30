from __future__ import annotations

from fastapi import APIRouter

from population.profile_builder import build_agent_profile_set
from schemas.population import AgentProfileSet, PopulationFitReport

router = APIRouter(prefix="/api/population", tags=["population"])


@router.get("/profile-set", response_model=AgentProfileSet)
def get_profile_set(
    platform_type: str = "wechat_minidrama",
    business_goal: str = "paid_conversion",
    distribution_id: str | None = None,
    max_agents: int = 6,
    seed: int = 42,
) -> AgentProfileSet:
    return build_agent_profile_set(
        platform_type=platform_type,
        business_goal=business_goal,
        distribution_id=distribution_id,
        max_agents=max_agents,
        seed=seed,
    )


@router.get("/fit-report", response_model=PopulationFitReport)
def get_fit_report(
    platform_type: str = "wechat_minidrama",
    business_goal: str = "paid_conversion",
    distribution_id: str | None = None,
    max_agents: int = 6,
    seed: int = 42,
) -> PopulationFitReport:
    return build_agent_profile_set(
        platform_type=platform_type,
        business_goal=business_goal,
        distribution_id=distribution_id,
        max_agents=max_agents,
        seed=seed,
    ).population_fit
