"""Writer Agent: generates candidate plot drafts.

Uses ScriptMind /api/plan (A2 策划 Agent) when available; falls back to
deterministic rule-based generation for demo stability.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from schemas.draft import CandidateDraft
from schemas.project import StoryProjectInput
from schemas.world_state import StoryWorldState

if TYPE_CHECKING:
    from llm.gateway import LLMGateway

logger = logging.getLogger(__name__)


def generate_candidate_drafts(
    input_data: StoryProjectInput,
    world: StoryWorldState,
    gateway: "LLMGateway | None" = None,
) -> list[CandidateDraft]:
    """编剧 Role：生成 3 套候选剧本草稿。

    调 ScriptMind /api/plan（工具层，见 ADR-0001）。请求参数完全由用户输入
    动态构造——genre 来自 input_data.genre，不写死默认值；protagonist 从
    story world 解析；platform 做映射；additional_notes 聚合作者意图、约束
    与编剧工作记忆中匹配当前平台/题材的经验模式。

    gateway 由 demo_runner 注入（生产用 LLMGateway，测试可注入 fake）。
    ScriptMind 不可达时降级到 rule-based fallback，保证 demo 不崩。
    """
    if gateway is None:
        logger.warning("编剧: 未注入 gateway，降级到 rule-based fallback")
        return _generate_rule_based(input_data, world)

    try:
        target_platform = _to_scriptmind_platform(input_data.platform_type)
        # genre 完全由用户输入决定；用户未填则传空串让 ScriptMind 自行处理，
        # 不再写死"悬疑"——那是上一个版本的占位。
        genre = input_data.genre[0] if input_data.genre else ""
        protagonist = _primary_character(world)
        notes = _build_notes(input_data, world)
        # 读取编剧工作记忆，注入匹配的经验模式（方向3：记忆接入主流程）
        notes = _inject_working_memory(notes, "screenwriter", input_data)

        plan_response = gateway.generate_candidate_drafts(
            genre=genre,
            protagonist_setting=protagonist,
            platform=target_platform,
            additional_notes=notes,
        )
        if plan_response and plan_response.drafts:
            logger.info(
                "编剧: ScriptMind /api/plan 返回 %d 套草稿",
                len(plan_response.drafts),
            )
            return gateway.map_plan_to_candidate_drafts(
                plan_response,
                author_goal=input_data.business_goal,
            )
        logger.warning("编剧: ScriptMind 返回空 drafts，降级到 rule-based")
    except Exception as exc:
        logger.warning("编剧: ScriptMind /api/plan 失败，降级到 rule-based: %s", exc)

    return _generate_rule_based(input_data, world)


def _to_scriptmind_platform(platform: str) -> str:
    """Map Drama Smallville platform type to ScriptMind platform."""
    mapping = {
        "fanqie": "douyin",
        "qidian": "wechat",
        "jinjiang": "weibo",
        "douyin_short_drama": "douyin",
        "kuaishou_short_drama": "douyin",
        "wechat_minidrama": "wechat",
        "other": "douyin",
    }
    return mapping.get(platform, "douyin")


def _build_notes(input_data: StoryProjectInput, world: StoryWorldState) -> str:
    parts: list[str] = []
    if input_data.materials.author_intent:
        parts.append(f"作者意图: {input_data.materials.author_intent}")
    if input_data.generation_request.must_keep_elements:
        parts.append(f"必须保留: {'、'.join(input_data.generation_request.must_keep_elements[:3])}")
    if input_data.generation_request.avoid_elements:
        parts.append(f"避免: {'、'.join(input_data.generation_request.avoid_elements[:3])}")
    parts.append(f"商业目标: {input_data.business_goal}")
    parts.append(f"当前冲突: {world.current_conflict[:120]}")
    return "；".join(parts) if parts else ""


# ── Rule-based fallback (original P0 logic) ──────────────────────────────────


def _generate_rule_based(
    input_data: StoryProjectInput,
    world: StoryWorldState,
) -> list[CandidateDraft]:
    count = input_data.generation_request.desired_candidate_count
    source = _story_source_text(input_data)
    protagonist = _primary_character(world)
    opponent = _opponent_character(world, protagonist)
    central_hook = _pick_first(world.hidden_information + world.unresolved_hooks, "关键真相尚未兑现")
    emotional_debt = _pick_first(world.emotional_debts, "情绪债需要兑现")
    conflict = _extract_conflict(source, world.current_conflict)
    conflict_fragment = _as_fragment(conflict)
    keep = _compact_list(input_data.generation_request.must_keep_elements, "保留核心冲突")
    avoid = _compact_list(input_data.generation_request.avoid_elements, "避免提前收束")
    platform_note = _platform_note(input_data.platform_type)
    goal = input_data.business_goal

    base = [
        CandidateDraft(
            draft_id="draft_a",
            title=f"线索压迫：{'证据链' if '证据' in central_hook else '下一步'}",
            synopsis=(
                f"{protagonist}围绕「{conflict}」先做克制推进，表面顺着{opponent}的节奏，"
                f"暗中把「{central_hook}」拆成可验证线索；结尾只亮出半个证据，逼观众继续追问。"
            ),
            key_beats=[
                f"复述当前冲突：{conflict}",
                f"保留：{keep}",
                f"避开：{avoid}",
                "结尾露出半个证据",
            ],
            intended_hook=f"{central_hook}到底指向谁",
            intended_emotion="克制、压迫、反击前夜",
            expected_reader_action="continue_reading",
            author_note=f"稳健型方案，适合{platform_note}的留存测试。",
        ),
        CandidateDraft(
            draft_id="draft_b",
            title=f"情绪摊牌：{'情感局' if '情感' in emotional_debt else '关系场'}",
            synopsis=(
                f"{protagonist}不急着解决事件，而是让{opponent}被迫回应「{emotional_debt}」。"
                f"双方只交换部分事实，保留「{central_hook}」作为下一段悬念。"
            ),
            key_beats=[
                f"先兑现情绪债：{emotional_debt}",
                "只承认一部分旧事",
                f"把{central_hook}留到下一轮",
            ],
            intended_hook=f"{opponent}还隐瞒了什么",
            intended_emotion="拉扯、委屈、迟疑、代入",
            expected_reader_action="give_positive_review",
            author_note="口碑型方案，优先提升人物情绪合理性。",
        ),
        CandidateDraft(
            draft_id="draft_c",
            title=f"公开反击：{'舆论场' if '舆论' in conflict else '反击局'}",
            synopsis=(
                f"{opponent}抢先把「{conflict}」推向公开危机，{protagonist}用前文保留的"
                f"「{central_hook}」完成反击卡点；本段不完全揭晓。"
            ),
            key_beats=[
                "对手抢先制造危机",
                f"主角调用保留元素：{keep}",
                "公开反击前卡点",
                f"避免：{avoid}",
            ],
            intended_hook=f"公开反击能否坐实{central_hook}",
            intended_emotion="危机、爽感、悬念",
            expected_reader_action="pay_to_unlock",
            author_note=f"付费型方案，适合{platform_note}的变现测试。",
        ),
    ]

    if goal == "positive_review":
        base = [base[1], base[0], base[2]]
    elif goal == "paid_conversion":
        base = [base[2], base[0], base[1]]

    return base[:count]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _story_source_text(input_data: StoryProjectInput) -> str:
    return (
        input_data.materials.current_draft
        or input_data.materials.previous_synopsis
        or input_data.materials.world_setting
        or input_data.title
    )


def _primary_character(world: StoryWorldState) -> str:
    for character in world.main_characters:
        if character.role in ("protagonist", "lead"):
            return character.name
    return world.main_characters[0].name if world.main_characters else "主角"


def _opponent_character(world: StoryWorldState, protagonist: str) -> str:
    for character in world.main_characters:
        if character.name != protagonist:
            return character.name
    return "关键关系人"


def _pick_first(items: list[str], fallback: str) -> str:
    return items[0] if items else fallback


def _extract_conflict(source: str, fallback: str) -> str:
    sentences = re.split(r"[。！？!?\n]", source)
    keywords = ["但", "却", "冲突", "隐瞒", "真相", "复仇", "危机", "背叛", "舆论", "证据"]
    for sentence in sentences:
        cleaned = sentence.strip()
        if 8 <= len(cleaned) <= 80 and any(keyword in cleaned for keyword in keywords):
            return cleaned
    return fallback[:80]


def _as_fragment(text: str) -> str:
    fragment = text.strip("。！？!? \n")
    fragment = re.sub(r"^(女主|男主|主角|她|他)?把所有人的反应重新想了一遍[。；，,]?", "", fragment)
    if len(fragment) > 46:
        fragment = fragment[:45].rstrip("，,；;、 ") + "..."
    return fragment or "眼前这场变故"


def _compact_list(items: list[str], fallback: str) -> str:
    return "、".join(items[:3]) if items else fallback


def _platform_note(platform_type: str) -> str:
    labels = {
        "wechat_minidrama": "微信短剧",
        "douyin_short_drama": "抖音短剧",
        "kuaishou_short_drama": "快手短剧",
        "fanqie": "番茄",
        "qidian": "起点",
        "jinjiang": "晋江",
        "other": "当前平台",
    }
    return labels.get(platform_type, "当前平台")


def _inject_working_memory(notes: str, role_id: str, input_data: StoryProjectInput) -> str:
    """读取 Role 工作记忆，把匹配当前平台/题材的经验模式追加到 notes。

    方向3：让 memory_store 不再是死代码。只注入 confidence >= 0.6 的 learned_patterns，
    且只取匹配当前 platform_type 的。低置信度记忆不进入运行上下文（见 Agent记忆层设计.md §6.4）。
    """
    try:
        from memory.memory_store import get_memory
        memory = get_memory(role_id)
        patterns = memory.get("learned_patterns", [])
        if not patterns:
            return notes
        matched: list[str] = []
        for p in patterns:
            # confidence 在 evidence 嵌套对象里（见 agent_memory/*.json 结构）
            evidence = p.get("evidence", {}) or {}
            conf = evidence.get("confidence", p.get("confidence", 0))
            if conf < 0.6:
                continue
            platforms = p.get("applies_to_platforms", [])
            # platform_type 字段在 learned_pattern 里存的是 DS 平台类型
            if platforms and input_data.platform_type not in platforms:
                continue
            desc = p.get("description", "")
            if desc:
                matched.append(desc)
        if matched:
            return notes + f"；编剧记忆: {'；'.join(matched[:2])}"
        return notes
    except Exception:
        # 记忆读取失败不应阻断主流程
        return notes
