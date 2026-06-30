from __future__ import annotations

from fastapi import APIRouter

from pydantic import BaseModel, Field

from schemas.project import GenerationRequest, StoryMaterials, StoryProjectInput
from schemas.report import StorySimulationReport
from services.demo_runner import run_demo

router = APIRouter(prefix="/api/drama", tags=["drama"])


class SimpleRunRequest(BaseModel):
    text: str
    title: str = "未命名故事"
    platform_type: str = "wechat_minidrama"
    business_goal: str = "paid_conversion"
    genre: list[str] = Field(default_factory=list)
    author_intent: str | None = None
    author_style: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    must_keep_elements: list[str] = Field(default_factory=list)
    avoid_elements: list[str] = Field(default_factory=list)


@router.post("/demo-run", response_model=StorySimulationReport)
def demo_run(input_data: StoryProjectInput) -> StorySimulationReport:
    return run_demo(input_data)


@router.post("/simple-run", response_model=StorySimulationReport)
def simple_run(request: SimpleRunRequest) -> StorySimulationReport:
    input_data = StoryProjectInput(
        project_id="simple_demo",
        title=request.title,
        format="short_drama",
        platform_type=request.platform_type,  # type: ignore[arg-type]
        genre=request.genre or ["短剧", "剧情测试"],
        business_goal=request.business_goal,  # type: ignore[arg-type]
        materials=StoryMaterials(
            character_bible="请根据用户输入自动识别主要角色。",
            world_setting="用户粘贴的故事材料为准。",
            previous_synopsis=request.text,
            current_draft=request.text,
            author_intent=request.author_intent,
            author_style=request.author_style or ["作者驱动", "虚拟试播"],
            constraints=request.constraints or ["不要替作者做最终决定", "输出可执行改稿建议"],
        ),
        generation_request=GenerationRequest(
            chapter_position="paid_conversion_point",
            desired_candidate_count=3,
            target_output="plot_direction",
            must_keep_elements=request.must_keep_elements or ["核心冲突", "人物动机", "下一步钩子"],
            avoid_elements=request.avoid_elements or ["强行完结", "无解释反转"],
        ),
    )
    return run_demo(input_data)
