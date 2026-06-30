# Drama Smallville 第一版 PRD：P0 技术实现路径

> 日期：2026-06-14  
> 定位：作者驱动的 AI 虚拟试播间 P0 版本  
> 目标：在路演前做出稳定可演示的第一版，同时把后续多 Agent 交互、真实反馈校准、Agent 记忆、RAG、OASIS-like 大规模仿真的接口边界预留好。  
> 原则：第一版只做能闭环的最小系统，不做全量平台；但所有核心抽象从第一天就按可扩展架构设计。

---

## 1. 一句话定位

Drama Smallville P0 是一个面向网文/短剧作者的 **AI 虚拟试播间**。

作者输入人物设定、前文剧情、当前节点和创作目标；系统生成 2-3 个候选剧情方案，先由创作参谋 Agent 检查剧作问题，再由虚拟观众和平台 Agent 模拟留存、好评、付费、平台推荐等反应，最后输出推荐方案、评分依据、分歧风险和改稿建议。

---

## 2. 产品边界

### 2.1 它是什么

- 剧情方案试播沙盘。
- 创作参谋 + 观众模拟的辅助工具。
- 多候选剧情比较器。
- 留存、好评、付费、平台推荐潜力的启发式评估器。
- 面向作者的改稿决策支持系统。

### 2.2 它不是什么

- 不是自动替作者写完整剧本的工具。
- 不是通用舆情系统。
- 不是承诺真实市场预测的系统。
- 不是操控评论区或平台推荐的工具。
- 不是第一版就做大规模 OASIS 仿真的系统。

### 2.3 作者是最终决策者

产品链路必须保留作者控制点：

```text
作者输入 / 系统生成候选
-> 创作参谋给建议
-> 作者确认或修改
-> 市场模拟
-> 作者决定采用、改写或放弃
```

任何 Agent 都不能直接替作者决定最终剧情。

### 2.4 Writer Agent 边界

Writer Agent 只负责生成“可比较的候选方案”，不负责生成最终稿。

P0 交互必须体现：

- 作者可以完全手写候选方案。
- 作者可以让系统生成候选方案。
- 系统生成的候选方案必须经过作者确认。
- 作者可以锁定人物设定、表达意图和不可改动情节。
- 市场模拟只能对“作者确认后的候选方案”运行。

因此 Writer Agent 的产品定位是：

```text
候选方案生成器
```

不是：

```text
自动剧本作者
```

---

## 3. P0 成功标准

P0 只证明一件事：

> 同一个剧情节点，系统能生成多个候选方案，并通过创作参谋 + 虚拟观众 + 平台视角，解释为什么某个方案更值得继续写。

P0 验收：

1. 用户可以输入人物设定、前文梗概、当前剧情节点、平台类型和创作目标。
2. Writer Agent 能生成 2-3 个候选剧情方案。
3. 创作参谋 Agent 能指出候选方案的剧作问题。
4. 用户可以选择确认或简单修改候选方案。
5. 市场模拟 Agent 能输出留存、好评、付费、平台推荐潜力。
6. Critic Agent 能挑战当前最高分方案。
7. Judge 能根据评分、分歧和风险输出最终推荐。
8. Report Agent 能生成可读报告。
9. 系统能保存完整 Trace。
10. 无模型 API 或模型失败时，Mock 模式仍可演示。

P0 的展示重点不是“功能数量”，而是主链路稳定：

```text
输入 -> 生成候选 -> 创作参谋 -> 作者确认 -> 观众模拟 -> 报告
```

如果时间不足，优先减少 Agent 数量，也不要破坏这条链路。

---

## 4. P0 不做什么

P0 暂不做：

- 完整 18 Agent。
- 复杂评论区传播网络。
- OASIS 原生接入。
- MiroFish 原生接入。
- 多模型路由的完整 UI。
- 真实平台数据接入。
- Agent Memory 自动学习。
- RAG 案例库。
- 复杂异步任务系统。
- PDF 导出。
- 团队协作和权限系统。

P0 只保留这些能力的接口和目录位置。

---

## 5. P0 最小 Agent 阵容

### 5.1 生成与解析

| Agent | 职责 |
|---|---|
| Story Parser Agent | 把用户材料整理成 StoryWorldState |
| Writer Agent | 生成 2-3 个候选剧情方案 |

### 5.2 创作参谋 Agent

P0 只做 2 个：

| Agent | 职责 |
|---|---|
| 连贯性编辑 Agent | 检查人设、伏笔、时间线、人物动机 |
| 爽点节奏 Agent | 检查爽点、反转、冲突、付费钩子 |

创作参谋 Agent 只能输出剧作建议，不输出市场概率。它们的结果在报告中必须放在 **Creative Review** 区块。

其他创作参谋 Agent 先预留：

- 情绪曲线 Agent。
- 类型片顾问 Agent。
- 作者审美守门 Agent。

### 5.3 市场模拟 Agent

P0 只做 4 个：

| Agent | 职责 |
|---|---|
| 爽点追更型观众 Agent | 判断冲突、打脸、反杀、追更意愿 |
| 情感代入型观众 Agent | 判断共情、情绪张力、好评倾向 |
| 付费解锁型观众 Agent | 判断 cliffhanger、付费钩子 |
| 平台推流 Agent | 判断平台推荐潜力、完读/评论/付费信号 |

市场模拟 Agent 只能输出观众行为概率和市场风险，不替作者改稿。它们的结果在报告中必须放在 **Audience Simulation** 区块。

其他市场 Agent 先预留：

- 悬念推理型读者 Agent。
- 下沉短剧快感型观众 Agent。
- 品质口碑型读者 Agent。
- 平台编辑 Agent。

### 5.4 聚合与解释

| Agent | 职责 |
|---|---|
| Critic Agent | 挑战当前最高分方案，指出失败风险 |
| Judge Agent | 聚合评分、分歧、风险和目标权重 |
| Report Agent | 生成面向作者的可读报告 |

---

## 6. P0 核心流程

```text
1. 用户输入项目材料
2. Story Parser Agent 生成 StoryWorldState
3. Writer Agent 生成 2-3 个 CandidateDraft
4. 创作参谋 Agent 对候选稿做剧作评审
5. 用户确认或快速修改候选稿
6. 市场模拟 Agent 进行 Round 1 独立评价
7. Light Simulator 生成环境摘要
8. 关键 Agent 根据环境摘要进行 Round 2 修正
9. Critic Agent 挑战当前最高分稿
10. Quality Evaluator 计算 DraftQualityScore
11. Judge Agent 输出最终推荐
12. Report Agent 生成报告
13. Trace Store 保存全过程
```

P0 可以串行执行。若时间允许，市场模拟 Agent 可并发执行。

### 6.1 P0 执行收敛规则

P0 实现时优先级如下：

1. 保证主流程能跑通。
2. 保证结构化 JSON 稳定。
3. 保证报告能解释推荐理由。
4. 保证 Trace 可复现。
5. 再增加更多 Agent 或更复杂交互。

如果工程时间不足，允许裁剪为：

```text
Story Parser
Writer Agent
连贯性编辑 Agent
爽点节奏 Agent
爽点追更型观众 Agent
付费解锁型观众 Agent
平台推流 Agent
Critic Agent
Judge / Report Agent
```

不可裁剪的是：

- 作者确认环节。
- 创作参谋与市场模拟分区。
- Quality Evaluator。
- Trace Store。

---

## 7. P0 技术架构

```text
Frontend
  -> Project Input
  -> Candidate Draft Workspace
  -> Creative Review
  -> Audience Simulation
  -> Decision Report

Backend
  -> API Layer
  -> StoryWorldState Builder
  -> LLM Gateway
  -> Markdown Agent Runtime
  -> Light Simulator
  -> Quality Evaluator
  -> Report Builder
  -> Trace Store
```

---

## 8. 核心 Schema

### 8.1 StoryProjectInput

```python
class StoryProjectInput(BaseModel):
    project_id: str
    title: str
    format: Literal["web_novel", "short_drama", "comic_script"]
    platform_type: Literal[
        "fanqie",
        "qidian",
        "jinjiang",
        "douyin_short_drama",
        "kuaishou_short_drama",
        "wechat_minidrama",
        "other",
    ]
    genre: list[str]
    business_goal: Literal[
        "retention",
        "positive_review",
        "paid_conversion",
        "platform_recommendation",
    ]
    materials: StoryMaterials
    generation_request: GenerationRequest
```

### 8.2 StoryMaterials

```python
class StoryMaterials(BaseModel):
    character_bible: str | None
    world_setting: str | None
    previous_synopsis: str | None
    current_draft: str | None
    author_intent: str | None
    author_style: list[str]
    constraints: list[str]
```

### 8.3 GenerationRequest

```python
class GenerationRequest(BaseModel):
    chapter_position: Literal[
        "opening",
        "early_hook",
        "mid_serial",
        "paid_conversion_point",
        "climax",
        "ending",
    ]
    chapter_index: int | None
    episode_index: int | None
    desired_candidate_count: int = 3
    target_output: Literal["plot_direction", "chapter_draft", "short_drama_scene"]
    must_keep_elements: list[str]
    avoid_elements: list[str]
```

### 8.4 StoryWorldState

```python
class StoryWorldState(BaseModel):
    project_id: str
    title: str
    genre: list[str]
    platform_type: str
    chapter_position: str
    main_characters: list[Character]
    relationships: list[Relationship]
    current_conflict: str
    unresolved_hooks: list[str]
    emotional_debts: list[str]
    hidden_information: list[str]
    power_dynamics: list[str]
    author_intent: str | None
    author_style: list[str]
    platform_context: dict
```

### 8.5 CandidateDraft

```python
class CandidateDraft(BaseModel):
    draft_id: str
    title: str
    synopsis: str
    script_text: str | None
    key_beats: list[str]
    intended_hook: str
    intended_emotion: str
    expected_reader_action: Literal[
        "continue_reading",
        "give_positive_review",
        "pay_to_unlock",
        "comment",
        "share",
    ]
    locked_by_author: bool = False
    author_note: str | None = None
```

### 8.6 CreativeReview

```python
class CreativeReview(BaseModel):
    agent_id: str
    draft_id: str
    score: float
    opinion: str
    suggested_revision: str
    must_fix: bool
    author_intent_conflict: bool
```

### 8.7 AudienceJudgment

```python
class AudienceJudgment(BaseModel):
    agent_id: str
    draft_id: str
    round_id: str
    continue_watch: float
    positive_review: float
    pay: float
    comment: float
    share: float
    dropoff: float
    platform_recommendation: float | None
    trigger_points: list[str]
    risk_points: list[str]
    revised_from_previous_round: bool
    revision_reason: str | None
    confidence: float
```

### 8.8 AgentMessage

```python
class AgentMessage(BaseModel):
    message_id: str
    round_id: str
    from_agent: str
    to_agent: str | Literal["all"]
    message_type: Literal[
        "draft",
        "creative_review",
        "judgment",
        "environment_feedback",
        "challenge",
        "revision",
        "judge_summary",
    ]
    content: str
    referenced_draft_id: str | None
    scores_delta: dict[str, float] | None
```

### 8.9 DraftQualityScore

```python
class DraftQualityScore(BaseModel):
    draft_id: str
    retention_score: float
    positive_review_score: float
    paid_conversion_score: float
    platform_recommendation_score: float
    logic_consistency_score: float
    character_consistency_score: float
    hook_strength_score: float
    emotional_intensity_score: float
    disagreement_penalty: float
    final_score: float
```

### 8.10 StorySimulationReport

```python
class StorySimulationReport(BaseModel):
    simulation_id: str
    recommended_draft_id: str
    initial_winner_draft_id: str
    winner_changed: bool
    confidence_score: float
    quality_scores: list[DraftQualityScore]
    creative_reviews: list[CreativeReview]
    audience_judgments: list[AudienceJudgment]
    key_disagreements: list[str]
    biggest_dropoff_risk: str
    strongest_paid_trigger: str
    platform_recommendation_summary: str
    confidence_level: Literal["high", "medium", "low"]
    confidence_reasons: list[str]
    no_strong_recommendation: bool
    rewrite_recommendations: list[str]
    next_iteration_prompt: str
```

### 8.11 低置信度机制

系统不能在所有情况下强行推荐一个方案。

以下情况应输出 `no_strong_recommendation = true`：

- 输入材料过少，无法建立清晰 `StoryWorldState`。
- 候选方案差异过小，无法有效比较。
- 所有候选方案质量分都低于阈值。
- Agent 分歧过大，且 Critic 指出致命风险。
- 平台类型未知，平台推荐判断置信度过低。

低置信度输出示例：

```text
当前没有强推荐方案。三个候选都存在明显问题：
1. 付费钩子不足；
2. 女主动机不清晰；
3. 平台推流信号弱。

建议先补充人物动机和章末钩子，再进入观众模拟。
```

---

## 9. Light Simulator P0 设计

P0 不实现完整社交网络，只实现最小环境反馈。

### 9.1 AgentProfile

每个观众/平台 Agent 都包含完整画像：

```text
基本人群信息
内容偏好
行为阈值
社交影响力
易受影响程度
记忆引用
```

### 9.2 AgentState

```python
class AgentState(BaseModel):
    attention: float = 5
    emotion: float = 5
    curiosity: float = 5
    trust: float = 5
    irritation: float = 0
    retention_intent: float = 0
    pay_intent: float = 0
    comment_intent: float = 0
    share_intent: float = 0
    dropoff_risk: float = 0
```

### 9.3 StoryEnvironment

```python
class StoryEnvironment(BaseModel):
    platform_heat: float = 0
    comment_velocity: float = 0
    positive_sentiment: float = 0
    negative_sentiment: float = 0
    controversy: float = 0
    recommendation_boost: float = 0
    top_comments: list[str] = []
    dominant_objections: list[str] = []
```

### 9.4 P0 环境摘要

市场模拟 Round 1 后，Light Simulator 汇总：

```text
哪些稿件获得最高留存
哪些稿件付费钩子最强
哪些风险被多个 Agent 提到
评论区可能出现什么高频吐槽
平台推荐信号是否强
```

Round 2 中，关键 Agent 读取这个摘要后可选择：

```text
保持评分
上调评分
下调评分
解释原因
```

这就是 P0 的最小交互闭环。

P0 的 Light Simulator 不能只做静态规则打分，必须至少展示一次反馈修正：

```text
Round 1：独立评价
Environment Summary：形成模拟评论区/平台环境摘要
Round 2：关键 Agent 读取摘要后保持、上调或下调评分
Critic Challenge：挑战当前最高分方案
```

报告中必须展示：

- 初始最高分方案。
- 最终推荐方案。
- 是否发生 winner change。
- 哪个 Agent 改变了评分。
- 改变原因。

---

## 10. 质量评分规则

### 10.1 付费目标

```text
final_score =
  0.30 * paid_conversion
  + 0.20 * hook_strength
  + 0.15 * emotional_intensity
  + 0.15 * retention
  + 0.10 * platform_recommendation
  + 0.10 * character_consistency
  - disagreement_penalty
```

### 10.2 留存目标

```text
final_score =
  0.30 * retention
  + 0.20 * emotional_intensity
  + 0.15 * hook_strength
  + 0.15 * logic_consistency
  + 0.10 * platform_recommendation
  + 0.10 * positive_review
  - disagreement_penalty
```

### 10.3 平台推荐目标

```text
final_score =
  0.30 * platform_recommendation
  + 0.25 * retention
  + 0.15 * comment
  + 0.15 * share
  + 0.15 * paid_conversion
  - disagreement_penalty
```

### 10.4 分歧惩罚

```text
disagreement_penalty =
  score_variance
  * critical_agent_weight
  * business_goal_sensitivity
```

P0 必须说明：

> 第一版权重为启发式规则，不代表真实市场统计。后续通过真实反馈校准。

这句话必须出现在报告页或报告底部。否则用户会误以为系统在承诺真实预测。

### 10.5 质量评分展示边界

报告里不要只展示总分，必须展示至少四个分区：

1. **Creative Review**：剧作层问题。
2. **Audience Simulation**：观众行为概率。
3. **Platform Fit**：平台推荐潜力与风险。
4. **Critic Risk**：最高分方案的失败条件。

这样可以避免把创作问题和市场反馈混成一个不可解释的总评。

---

## 11. LLM Gateway

所有 Agent 调用模型必须走统一接口：

```python
llm.generate_json(
    model_id="default_llm",
    prompt=prompt,
    schema=TargetSchema,
)
```

P0 可以只接一个模型：

```yaml
models:
  default_llm:
    provider: openai_compatible
    base_url: ${MODEL_BASE_URL}
    api_key_env: MODEL_API_KEY
    model: ${MODEL_NAME}
```

但目录和配置必须支持后续多模型：

```yaml
agents:
  writer:
    model_id: default_llm
  creative_continuity:
    model_id: default_llm
  paid_unlock_viewer:
    model_id: default_llm
  judge:
    model_id: default_llm
```

P0 必须实现：

- JSON schema validation。
- JSON repair。
- retry。
- timeout。
- mock fallback。

P0 正式路演不建议全部使用 Mock。至少以下模块应尽量走真实模型：

- Writer Agent。
- 创作参谋 Agent。
- Report Agent。

市场模拟 Agent 可以部分规则化或 Mock 化，但报告必须明确哪些结果来自模型、哪些来自规则。

---

## 12. Agent Markdown 与 Memory

### 12.1 Agent Markdown

P0 使用 Markdown 定义 Agent：

```text
agents_md/
  story_parser.md
  writer.md
  creative_continuity.md
  creative_pacing.md
  audience_shuangwen.md
  audience_emotion.md
  audience_paid_unlock.md
  platform_distribution.md
  critic.md
  judge.md
  report_agent.md
```

### 12.2 Agent Memory

P0 只做空 memory 文件和读取接口。

```text
storage/agent_memory/{agent_id}.json
```

暂不做自动学习。

后续真实反馈进入：

```text
RealFeedback
-> CalibrationRecord
-> 人工/规则审核
-> AgentMemory
```

---

## 13. Trace Store

P0 必须保存：

```text
simulation_id
schema_version
input
story_world_state
candidate_drafts
creative_reviews
audience_judgments
agent_messages
quality_scores
final_report
model_config
prompt_versions
created_at
```

Trace 是后续调试、复盘、校准和商业化的基础。

P0 验收时必须能查看一条 Trace，至少包含：

- 原始输入。
- 生成的候选稿。
- 每个 Agent 的输出。
- 环境摘要。
- Critic challenge。
- 质量评分。
- 最终报告。

---

## 14. API 设计

### 14.1 创建项目

```http
POST /api/drama/projects
```

### 14.2 上传/解析剧情

```http
POST /api/drama/projects/{project_id}/story-context
```

### 14.3 生成候选稿

```http
POST /api/drama/projects/{project_id}/candidate-drafts/generate
```

### 14.4 创作参谋评审

```http
POST /api/drama/projects/{project_id}/creative-review
```

### 14.5 作者提交修改

```http
POST /api/drama/projects/{project_id}/candidate-drafts/{draft_id}/revise
```

### 14.6 启动观众模拟

```http
POST /api/drama/projects/{project_id}/audience-simulations
```

### 14.7 获取报告

```http
GET /api/drama/audience-simulations/{simulation_id}/report
```

P0 可以先将这些 API 合并成一个：

```http
POST /api/drama/demo-run
```

但内部代码仍按上述模块拆分。

---

## 15. 前端 P0

P0 前端只做 3 个主区：

1. **输入区**  
   人物设定、前文梗概、当前节点、作者意图、平台类型、商业目标。

2. **候选与评审区**  
   展示 2-3 个候选稿，创作参谋意见，作者可选择“一键应用建议”。

3. **虚拟试播报告区**  
   展示推荐稿、质量评分、留存/好评/付费/平台推荐、Critic 风险、改稿建议。

可选开发者区：

- Raw JSON input。
- Raw JSON output。
- Trace preview。

前端不能只展示一段长报告，否则用户会觉得它像普通 ChatGPT。P0 至少要可视化：

- 候选方案 A/B/C 对比。
- Creative Review 和 Audience Simulation 分区。
- 初始最高分 vs 最终推荐。
- 留存/好评/付费/平台推荐四项指标。
- Critic 风险卡片。
- 一键应用改稿建议。

---

## 16. 文件结构

```text
script simulation/
  第一版PRD-P0技术实现路径.md
  backend/
    api/
      drama_routes.py
    schemas/
      project.py
      world_state.py
      draft.py
      creative_review.py
      judgment.py
      message.py
      quality.py
      report.py
      trace.py
    llm/
      gateway.py
      json_repair.py
      model_registry.py
    agents/
      base.py
      story_parser.py
      writer.py
      creative_advisors.py
      audience_agents.py
      platform_agents.py
      critic.py
      judge.py
      report_agent.py
    agents_md/
      story_parser.md
      writer.md
      creative_continuity.md
      creative_pacing.md
      audience_shuangwen.md
      audience_emotion.md
      audience_paid_unlock.md
      platform_distribution.md
      critic.md
      judge.md
      report_agent.md
    simulation/
      agent_profile.py
      agent_state.py
      story_environment.py
      light_simulator.py
      feed_simulator.py
      quality_evaluator.py
      emergence_metrics.py
    storage/
      trace_store.py
      agent_memory/
    services/
      author_revision_service.py
  frontend/
```

---

## 17. 后续扩展接口

P0 必须预留，但不实现完整能力：

| 后续能力 | P0 预留方式 |
|---|---|
| 多模型 | `model_id` 配置 |
| Agent Memory | `storage/agent_memory/` |
| RAG 案例库 | `retrieval/` 目录预留 |
| OASIS-like 大规模仿真 | `engine/oasis_adapter.py` 预留 |
| 真实反馈校准 | `RealFeedback` / `CalibrationRecord` Schema 预留 |
| 异步任务 | `simulation_id` 和 status 字段预留 |
| 报告导出 | Report schema 支持 markdown 字段 |

---

## 18. P0 Demo 脚本

输入：

```text
第 8 集末尾，女主已经发现男主当年隐瞒真相，但还不知道真正幕后黑手是养父。作者希望女主保持清醒强势，不要立刻原谅男主。
```

Writer Agent 生成：

```text
A：女主假意合作，暗中设局。
B：男主自爆旧事，求女主原谅。
C：养父反杀，女主陷入舆论危机。
```

创作参谋指出：

```text
B 违背作者“不立刻原谅”的表达。
C 商业钩子强，但要补女主提前察觉的细节，否则显得被动。
```

作者一键应用建议：

```text
C'：养父制造偷拍视频反咬女主，但女主其实提前埋下证据，准备在直播发布会上反杀。
```

市场模拟输出：

```text
推荐方案：C'
追更概率：84%
付费概率：67%
讨论概率：76%
弃坑风险：19%

原因：
它保留舆论危机的强冲突，也让女主保持主动掌控，兼顾作者审美和市场钩子。
```

---

## 19. 最大风险

1. **范围膨胀**：不要第一版实现全量 Agent、OASIS、RAG、真实数据校准。
2. **JSON 不稳定**：必须有 schema validation、repair、retry、mock fallback。
3. **评分伪科学**：必须说明 P0 权重是启发式，后续真实反馈校准。
4. **作者被边缘化**：必须保留作者修改/确认环节。
5. **Agent 混用**：创作参谋不模拟市场，市场模拟不替作者改稿。
6. **路演太慢**：P0 Agent 数量必须收敛，可并发则并发。
7. **Light Simulator 像静态打分器**：必须展示环境摘要和至少一次评分修正。
8. **强行推荐坏方案**：必须支持低置信度和无强推荐输出。
9. **全部 Mock 导致真实感不足**：正式演示至少部分 Agent 走真实模型。

---

## 20. 结论

P0 的核心不是做完整仿真平台，而是做一个稳定闭环：

```text
作者输入
-> 生成候选
-> 创作参谋指出剧作问题
-> 作者确认
-> 虚拟观众试播
-> 输出推荐和改稿建议
```

这个版本足够证明产品价值，也为后续：

- 多模型。
- Agent Memory。
- RAG。
- 真实反馈校准。
- OASIS-like 大规模仿真。
- 商业化创作工作台。

保留了清晰接口。
