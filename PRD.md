# Drama Smallville — 短剧虚拟试播台 PRD

> 本文件是本项目**唯一**的 PRD 文档。此前分散的 P0/P1/MiroFish/记忆层/传播学 Layer 等多份 PRD 已合并于此，原件已归档至 `docs/archive/`。
>
> 最后更新：2026-06-28

---

## 0. 一句话定位

一个把短剧/网文剧情草稿送进虚拟观众群**试播**、收集反应、给出改稿建议的多 Agent 系统。剧组 Agent 集群负责生产内容，观众 Agent 集群负责产生反应，两个集群通过"试播"这个动作耦合。

> **作者输入 → 编剧生成候选草稿 → 剧本医生审稿 → 观众群试播 → 输出推荐与改稿建议**

---

> **路径约定与模块布局**：本 PRD 中所有 backend 代码路径均相对于 `script simulation/backend/`。实际模块分布（并非全部在 `simulation/` 下）：
> - `schemas/` — Pydantic 数据模型（project / draft / judgment / quality / report / population 等）
> - `population/` — 观众群管线（`sampler.py` / `compressor.py` / `validator.py` / `profile_builder.py`）
> - `agents/` — 剧组与观众 Role（`screenwriter.py` / `script_doctor.py` / `audience_agents.py` / `judge.py` / `story_parser.py`）
> - `services/` — 编排（`demo_runner.py`）
> - `simulation/` — 评分与环境（`quality_evaluator.py` / `agent_profile.py` / `light_simulator.py` / `story_environment.py`）
> - `llm/` — ScriptMind 网关（`gateway.py` / `script_mind_client.py`）
> - `memory/`、`storage/`、`api/`、`tests/`、`agents_md/`、`config/`
>
> 例：`simulation/quality_evaluator.py` 的实际位置是 `script simulation/backend/simulation/quality_evaluator.py`。

## 1. 两个集群（顶层架构）

### 1.1 剧组 (Production Crew)

生产短剧内容的 Role 集合，按真实剧组职位分工组织。**现阶段最小集为 2 个 Role**：

| Role | 职责 | 调用的 ScriptMind 端点 |
|---|---|---|
| 编剧 (Screenwriter) | 用户输入 + 创作意图 → 动态构造请求 → 拿 3 套草稿 | `/api/plan` |
| 剧本医生 (Script Doctor) | 对 3 套草稿做连贯性 + 节奏双维度评审，拿 LLM 改稿建议 | `/api/generate` |

**已砍掉的 Role**：分镜师。理由：ScriptMind 无分镜端点（违背 ADR-0001）；分镜与剧本是接力非并行；优先级低于大纲和剧本。

### 1.2 观众群 (Audience Population)

依现实数据调参的 Persona 集合，每个 Persona 带权重，模拟复杂世界的观众反应分布。由人口采样（Categorical/Bernoulli/Beta/Dirichlet 四种分布）+ KMeans 聚类压缩产生 4-6 个代表性 Persona，配 PopulationFitReport 拟合误差报告。

### 1.3 并行点（多 Agent 并行合作的真正位置）

并行不靠剧组成员数量堆，而在以下三处：

1. ScriptMind `/api/plan` 一次返回 3 套草稿 = 3 个并行草稿产物
2. 剧本医生对 3 套草稿的审稿可 `asyncio.gather` 并行
3. 观众群多 Persona × 多 Draft 的 Judgment 是 O(Persona×Draft) 并行矩阵

---

## 2. 工具层：ScriptMind（ADR-0001）

ScriptMind 作为外部工具层，提供 LLM 驱动的三个端点：

| 端点 | 背后 LLM 工作 | 调用方 |
|---|---|---|
| `POST /api/plan` | DeepSeek v3.1 生成 3 套剧本大纲 | 编剧 |
| `POST /api/generate` | LLM 生成改稿建议 | 剧本医生 |
| `POST /api/extract-features` | LLM 语义分析内容特征 | 预留 |

**不自建 LLM Key**。请求参数根据用户输入文本**动态构造**，不写死 JSON。

### 2.1 连通性现状（2026-06-28 验证）

- 网络通：能到达 `scriptmind-50bc6328.eazo.dev`
- `/api/plan`：返回 500 `PLAN_FAILED`（ScriptMind 后端 LLM 生成失败）
- `/api/extract-features` / `/api/generate`：返回 400（请求格式待对齐）
- **降级机制工作正常**：所有端点失败时，编剧走 rule-based fallback，剧本医生走纯规则评审，demo 不崩

### 2.2 降级策略

每个 Role 调 ScriptMind 失败时降级到规则引擎。降级路径已测试通过。ScriptMind 恢复后自动切回 LLM。

---

## 3. 工作记忆（方向3）

每个 Role 拥有**针对性设计**的工作记忆，不共享通用 schema。

### 3.1 记忆分层

| 层 | 位置 | 特点 |
|---|---|---|
| 稳定角色设定 | `agents_md/{role}.md` | 人工维护，不自动更新 |
| 工作记忆 | `storage/agent_memory/{role}.json` | 可通过 API 更新，带 evidence/confidence |
| 会话级短期记忆 | `SimulationState.messages` | 只在本次试播生效 |
| 真实反馈 | `storage/feedback/` | **尚未实现**（见 §3.4 待办）；规划中优先级高于纯模拟结果 |

### 3.2 运行时注入（已接入主流程）

编剧调 `/api/plan` 前，读取自己的工作记忆，把匹配当前 `platform_type` 且 `confidence >= 0.6` 的 learned_patterns 追加到 additional_notes。低置信度记忆不进入运行上下文。

### 3.3 防污染机制

- 模拟结果只进 Trace，不直接写 learned_patterns
- 长期记忆来源优先级：`real_feedback > manual > repeated_simulation > single_simulation`
- 所有记忆必须带 source / confidence / applies_to_platforms

### 3.4 待办

- [ ] 剧本医生工作记忆 schema 设计（当前用通用 learned_patterns）
- [ ] 试播结束后把观察到的模式写回记忆（当前只读不写）
- [ ] 真实反馈导入 → CalibrationRecord → 审核后写入长期记忆

---

## 4. 核心流程

```text
1. 用户输入 StoryProjectInput（人物、前文、当前节点、商业目标）
2. Story Parser 解析成 StoryWorldState
3. 编剧 Role 调 /api/plan（注入工作记忆）→ 3 套 CandidateDraft
   ├─ ScriptMind 不可达 → rule-based fallback
4. 剧本医生 Role 调 /api/generate → 连贯性 + 节奏双维度 CreativeReview
   ├─ ScriptMind 不可达 → 纯规则评审
5. 观众群构建：采样 → KMeans 压缩 → 4-6 个 Persona + PopulationFitReport
6. Round 1：每个 Persona × 每个 Draft → AudienceJudgment（6 维度）
7. Light Simulator 生成环境摘要
8. Round 2：关键 Persona 读环境摘要后微调判断
9. Quality Evaluator 计算 DraftQualityScore
10. Critic 挑战最高分方案
11. Judge 聚合 → StorySimulationReport（含置信度、改稿建议）
12. Trace Store 保存全过程
```

---

## 5. 核心Schema

### StoryProjectInput → StoryWorldState → CandidateDraft → CreativeReview / AudienceJudgment → DraftQualityScore → StorySimulationReport

完整 schema 定义见 `schemas/`（路径相对于 `script simulation/backend/`）。关键字段：

- **AudienceJudgment**: continue_watch / positive_review / pay / comment / share / dropoff 六维度 + trigger_points / risk_points
- **DraftQualityScore**: 按商业目标（retention/paid_conversion/positive_review/platform_recommendation）不同权重聚合
- **StorySimulationReport**: recommended_draft_id + confidence_score + confidence_level + rewrite_recommendations
- **低置信度机制**: `no_strong_recommendation = true` 当输入不足、候选差异过小、Agent 分歧过大时

---

## 6. 质量评分规则

按商业目标不同权重（详见 `simulation/quality_evaluator.py`）：

```text
paid_conversion: 0.30*pay + 0.20*hook + 0.15*emotion + 0.15*retention + 0.10*platform + 0.10*character - disagreement
retention:       0.30*retention + 0.20*emotion + 0.15*hook + 0.15*logic + 0.10*platform + 0.10*positive - disagreement
```

> ⚠️ 第一版权重为启发式规则，不代表真实市场统计。后续通过真实反馈校准。此声明必须出现在报告底部。

---

## 7. 待办路线图（来自项目拷问总结）

### 7.1 方向1：语义清理（进行中）

- [x] 归档 `品牌舆情推演.md`（解决两个 PRD 互相否定）
- [x] 砍掉分镜师，定剧组 2 Role
- [x] CONTEXT.md 定义 9 个术语，禁用裸 "Agent"
- [x] 文件重命名：`writer.py` → `screenwriter.py`，`critic.py` → `script_doctor.py`
- [ ] `AgentProfile` → `PersonaProfile`（消除与 LLM Agent 的重载）
- [ ] `confidence = 0.72` 硬编码 → 写 ADR 记录来源，P1 用真实数据替换

### 7.2 方向2：ScriptMind 工具层（进行中）

- [x] `demo_runner.run_demo` 注入 gateway 参数，ScriptMind 真正被调通
- [x] 删除假接口 `generate_json`（收 prompt 不用的橱窗）
- [x] writer 的 genre 参数动态化（不再写死"悬疑"）
- [x] 剧本医生（creative_advisors）调 ScriptMind 链路接通（改用 /api/extract-features）
- [x] 排查 ScriptMind 三端点 500/400：genre 需英文枚举（已加 _normalize_genre 映射）；响应字段名修复（outline→acts, hookPoints→hooks）；extract-features 需 50+ 字且 features 嵌套层修复
- [ ] `/api/extract-features` 接入观众群特征提取
- [ ] asyncio.gather 并行化剧本医生对 3 套草稿的审稿

### 7.3 方向3：工作记忆（进行中）

- [x] `memory_store` 接入编剧主流程（读取 + 注入 additional_notes）
- [x] 编剧工作记忆种子文件（2 条 manual_expert 模式）
- [x] confidence >= 0.6 才注入，低置信度不进入运行上下文
- [ ] 剧本医生工作记忆 schema 设计
- [ ] 试播结束后写回观察到的模式（当前只读不写）
- [ ] Persona 工作记忆接入 `_judge_draft`

### 7.4 可测试性（严重缺失 → 已补首批）

- [x] `run_demo` 和 `run_creative_reviews` 支持注入 gateway（测试可传 fake）
- [x] 给 `_judge_draft`（183 行上帝函数）拆成 `_build_judge_text` + `_score_keywords` + `_apply_goal_boost` + `_generate_risks_triggers`
- [x] 写 `make_test_world()` / `make_test_draft()` / `make_test_persona()` 工厂函数（`tests/factories.py`）
- [x] 首批测试：sampler / compressor / validator（19 个测试全过，`tests/test_pipeline.py`）
- [ ] Trace 回放与对比功能（当前只有 save_trace，无 load/compare）

### 7.5 ADR

- [x] ADR-0002: ScriptMind 不可达时的降级策略
- [x] ADR-0003: KMeans 压缩人口的选择理由（vs GMM / 分层聚类）
- [x] ADR-0004: Round 2 只选 6 个 key_agents 的理由

---

## 8. 已归档的文档

以下文档已合并到本 PRD 或归档，不再作为独立 PRD 维护：

| 原文档 | 去向 | 保留的价值 |
|---|---|---|
| `品牌舆情推演.md` | `docs/品牌舆情推演_已归档.md` | 定位已转向短剧，舆情推演是未实现方向 |
| `script simulation/第一版PRD-P0技术实现路径.md` | 合并到本 PRD §4-§6 | 核心流程、Schema、质量评分规则、低置信度机制 |
| `script simulation/P1-统计拟合Agent画像PRD.md` | 合并到本 PRD §1.2、§3 | 统计拟合管线、记忆分层、P1 借鉴结论 |
| `script simulation/MiroFish架构借鉴PRD.md` | 合并到本 PRD §1、§4 | StoryWorldState、SimulationState、Trace、Report 分离 |
| `script simulation/Agent记忆层设计.md` | 合并到本 PRD §3 | 记忆分层、防污染、运行时注入、置信度阈值 |
| `script simulation/传播学Layer适配建议.md` | 合并到本 PRD §5（质量评分）| Need/Frame/State/Threshold Layer 框架（轻量采用）|

---

## 9. 最大风险

1. **ScriptMind 单点依赖**：它挂了剧组就停摆（ADR-0001 已记录）。降级机制是必要的。
2. **评分伪科学**：P0 权重是启发式，必须声明，后续真实反馈校准。
3. **作者被边缘化**：必须保留作者修改/确认环节，任何 Role 都不能替作者决定最终剧情。
4. **范围膨胀**：不要第一版就做全量 Role、OASIS、RAG、真实数据校准。
5. **记忆自我强化**：模拟结果不能直接写回长期记忆，需审核。

---

## 10. 结论

P0 的核心不是做完整仿真平台，而是做一个稳定闭环：

```text
作者输入 → 编剧生成候选 → 剧本医生审稿 → 观众群试播 → 输出推荐和改稿建议
```

这个版本足够证明产品价值，也为后续（多模型、Agent Memory、RAG、真实反馈校准、大规模仿真）保留了清晰接口。
