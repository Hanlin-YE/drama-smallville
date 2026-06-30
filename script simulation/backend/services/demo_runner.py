from __future__ import annotations

from uuid import uuid4

from agents.audience_agents import run_round_one, run_round_two
from agents.creative_advisors import run_creative_reviews
from agents.script_doctor import challenge_top_draft
from agents.judge import build_report
from agents.story_parser import parse_story_world
from agents.screenwriter import generate_candidate_drafts
from config.settings import settings
from llm.gateway import LLMGateway
from schemas.message import AgentMessage
from schemas.project import StoryProjectInput
from schemas.report import StorySimulationReport
from population.profile_builder import build_agent_profile_set
from simulation.agent_profile import from_representative_agents
from schemas.trace import TraceRecord
from simulation.light_simulator import build_environment
from simulation.quality_evaluator import evaluate_quality
from storage.trace_store import save_trace


def run_demo(
    input_data: StoryProjectInput,
    gateway: LLMGateway | None = None,
) -> StorySimulationReport:
    simulation_id = f"sim_{uuid4().hex[:10]}"
    world = parse_story_world(input_data)
    # 注入 gateway：传入则用传入的（测试可注入 fake），否则创建实例调 ScriptMind。
    # 不再默认走 rule-based fallback——ScriptMind 是工具层（ADR-0001）。
    llm_gateway = gateway or LLMGateway()
    drafts = generate_candidate_drafts(input_data, world, gateway=llm_gateway)
    creative_reviews = run_creative_reviews(world, drafts, gateway=llm_gateway)
    profile_set = build_agent_profile_set(
        platform_type=input_data.platform_type,
        business_goal=input_data.business_goal,
        max_agents=6,
        seed=42,
    )
    agent_profiles = from_representative_agents(profile_set.representative_agents)

    round_one = run_round_one(world, drafts, agent_profiles)
    env = build_environment(round_one)
    round_two = run_round_two(world, drafts, round_one, env)
    judgments = round_one + round_two

    quality_scores = evaluate_quality(input_data.business_goal, judgments, creative_reviews)
    critic_message = challenge_top_draft(drafts, quality_scores)
    messages = _messages_from_outputs(drafts, creative_reviews, judgments, critic_message)

    report = build_report(
        simulation_id=simulation_id,
        business_goal=input_data.business_goal,
        drafts=drafts,
        quality_scores=quality_scores,
        creative_reviews=creative_reviews,
        audience_judgments=judgments,
        critic_message=critic_message,
        env_by_draft=env,
    )
    trace = TraceRecord(
        simulation_id=simulation_id,
        schema_version=settings.schema_version,
        input=input_data,
        story_world_state=world,
        candidate_drafts=drafts,
        creative_reviews=creative_reviews,
        audience_judgments=judgments,
        agent_messages=messages,
        quality_scores=quality_scores,
        final_report=report,
        model_settings={
            "model": settings.model_name,
            "mode": "mock_or_configured",
            "profile_set_id": profile_set.profile_set_id,
            "population_fit": profile_set.population_fit.model_dump(mode="json"),
        },
        prompt_versions={"p0": "markdown-agent-v1"},
    )
    save_trace(trace)
    return report


def _messages_from_outputs(
    drafts,
    reviews,
    judgments,
    critic_message,
) -> list[AgentMessage]:
    messages: list[AgentMessage] = []
    for draft in drafts:
        messages.append(
            AgentMessage(
                message_id=f"msg_draft_{draft.draft_id}",
                round_id="writer",
                from_agent="writer",
                to_agent="all",
                message_type="draft",
                content=f"{draft.title}: {draft.synopsis}",
                referenced_draft_id=draft.draft_id,
            )
        )
    for review in reviews:
        messages.append(
            AgentMessage(
                message_id=f"msg_review_{review.agent_id}_{review.draft_id}",
                round_id="creative_review",
                from_agent=review.agent_id,
                to_agent="writer",
                message_type="creative_review",
                content=review.opinion,
                referenced_draft_id=review.draft_id,
            )
        )
    for judgment in judgments:
        if judgment.round_id == "round_2":
            messages.append(
                AgentMessage(
                    message_id=f"msg_revision_{judgment.agent_id}_{judgment.draft_id}",
                    round_id="round_2",
                    from_agent=judgment.agent_id,
                    to_agent="judge",
                    message_type="revision",
                    content=judgment.revision_reason or "保持判断。",
                    referenced_draft_id=judgment.draft_id,
                )
            )
    messages.append(critic_message)
    return messages
