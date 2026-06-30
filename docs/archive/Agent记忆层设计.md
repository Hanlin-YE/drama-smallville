# Agent 记忆层设计

> 日期：2026-06-13  
> 目标：为每个 Agent 建立可独立维护、可实时反馈更新、可审计回滚的记忆文档，使 Agent 不只是一次性 prompt，而能根据历史模拟结果和真实数据逐步校准。

---

## 1. 核心判断

每个 Agent 都应该有自己的记忆文档，但记忆不能无控制地自动污染角色判断。

推荐原则：

```text
Agent Markdown = 稳定角色设定
Agent Memory = 可更新经验
Simulation Trace = 每次运行记录
Real Feedback = 真实数据反馈
```

Agent 的最终上下文由四部分组成：

```text
角色说明书
+ 当前剧情世界状态
+ 当前候选稿件
+ Agent 专属记忆
+ 本轮交互消息
```

这样既保留 Agent 的稳定人格，又允许它根据实时数据逐渐变聪明。

---

## 1.1 第一性原理：架构先完整，实现分阶段

Agent 记忆系统的底层不变量是：

```text
真实世界反馈会持续进入系统，而系统必须能吸收反馈、校准 Agent、保留证据、回滚错误更新。
```

因此，**架构层必须从第一天按终局设计**。也就是说，即使 P0/P1 暂时只用少量 Agent、少量 JSON 文件和人工输入，也必须提前定义好：

- AgentProfile。
- AgentMemory。
- RealFeedback。
- CalibrationRecord。
- SimulationTrace。
- Evidence / confidence / source。
- 版本号和回滚机制。

否则后面一旦接入真实完读率、付费率、评论数据、平台反馈和客户私有数据，就会发现早期记忆只是散落的 prompt 或临时 JSON，需要推倒重来。

但 **实现层不能一口吃完**。完整商业化记忆系统包含真实数据接入、自动校准、向量检索、跨项目学习、权限隔离和审计工作流，这些不应该在 P0/P1 全部实现。

正确策略是：

```text
架构层：按商业化终局建模
实现层：按 P0/P1/P2 逐步打开能力
```

对应到当前阶段：

```text
P0：建立目录、Schema、空 memory 文件、trace 保存
P1：支持手动读写 Agent Memory，并记录 evidence/source/confidence
P2：接入真实反馈，生成 CalibrationRecord
P3：审核后更新 Agent Memory，支持回滚和版本管理
P4：接入私有数据、向量检索和自动校准
```

一句话原则：

> **不要用临时实现决定未来架构；也不要用未来架构拖垮当前实现。**

---

## 2. 记忆分层

### 2.1 稳定角色记忆

位置：

```text
agents_md/{agent_id}.md
```

内容：

- 角色身份。
- 代表人群。
- 固定偏好。
- 固定厌恶点。
- 评分原则。
- 输出 Schema。
- 语气风格。

特点：

- 人工维护。
- 不自动更新。
- 版本化。
- 相当于 Agent 的“人格设定”。

---

### 2.2 Agent 专属经验记忆

位置：

```text
storage/agent_memory/{agent_id}.json
```

内容：

- 历史判断偏差。
- 哪些剧情类型曾经高估/低估。
- 真实反馈校准结果。
- 该 Agent 最近学到的模式。
- 该 Agent 在不同平台/题材下的权重修正。

特点：

- 可通过接口更新。
- 默认不直接覆盖角色说明书。
- 需要记录来源和置信度。
- 可以回滚。

---

### 2.3 会话级短期记忆

位置：

```text
SimulationState.messages
```

内容：

- 本次模拟中其他 Agent 的观点。
- 反驳、同意、修正消息。
- Writer Agent 的改稿过程。
- Judge 的中间判断。

特点：

- 只在本次模拟中生效。
- 不自动写入长期记忆。
- 可以作为 trace 保存。

---

### 2.4 真实反馈记忆

位置：

```text
storage/feedback/{project_id}.json
```

来源：

- 实际完读率。
- 追更率。
- 好评率。
- 评论关键词。
- 付费转化。
- 平台推荐结果。
- 用户人工反馈。

特点：

- 优先级高于纯模拟结果。
- 可用于校准 Agent 记忆。
- 写入 Agent Memory 前需要经过筛选。

---

## 3. Agent Memory Schema

```python
class AgentMemory(BaseModel):
    agent_id: str
    memory_version: str
    updated_at: str
    stable_traits: list[str]
    learned_patterns: list[LearnedPattern]
    calibration_notes: list[CalibrationNote]
    platform_adjustments: dict[str, float]
    genre_adjustments: dict[str, float]
    confidence: float
```

```python
class LearnedPattern(BaseModel):
    pattern_id: str
    description: str
    applies_to_genres: list[str]
    applies_to_platforms: list[str]
    signal: str
    expected_effect: str
    confidence: float
    source: Literal["manual", "simulation", "real_feedback"]
    created_at: str
```

```python
class CalibrationNote(BaseModel):
    note_id: str
    project_id: str
    original_prediction: dict[str, float]
    actual_feedback: dict[str, float]
    error_summary: str
    adjustment_suggestion: str
    accepted: bool
    created_at: str
```

---

## 4. 记忆更新接口

### 4.1 查询 Agent 记忆

```http
GET /api/agents/{agent_id}/memory
```

返回：

```json
{
  "agent_id": "paid_unlock_audience",
  "memory_version": "v1",
  "learned_patterns": [],
  "calibration_notes": [],
  "confidence": 0.72
}
```

---

### 4.2 追加经验记忆

```http
POST /api/agents/{agent_id}/memory/patterns
```

请求：

```json
{
  "description": "在微信小程序短剧中，身份揭露前一集如果保留明确未完成信息，付费解锁意愿通常上升。",
  "applies_to_genres": ["复仇", "甜虐", "家庭伦理"],
  "applies_to_platforms": ["wechat_minidrama"],
  "signal": "身份线索未完全揭露",
  "expected_effect": "paid_conversion_score +0.08",
  "confidence": 0.68,
  "source": "real_feedback"
}
```

---

### 4.3 写入真实反馈校准

```http
POST /api/agents/{agent_id}/memory/calibrations
```

请求：

```json
{
  "project_id": "story_001",
  "original_prediction": {
    "paid_conversion": 0.81,
    "retention": 0.76
  },
  "actual_feedback": {
    "paid_conversion": 0.62,
    "retention": 0.74
  },
  "error_summary": "付费解锁型 Agent 高估了身份揭露钩子的付费转化。",
  "adjustment_suggestion": "当上一集已经泄露过同类身份线索时，下调 paywall_value 权重。",
  "accepted": false
}
```

---

### 4.4 审核并接受校准

```http
POST /api/agents/{agent_id}/memory/calibrations/{note_id}/accept
```

作用：

- 人工或系统审核后，将校准建议转化为 learned pattern 或权重调整。
- 避免一次异常真实数据直接污染长期记忆。

---

### 4.5 回滚记忆版本

```http
POST /api/agents/{agent_id}/memory/rollback
```

请求：

```json
{
  "target_version": "v3"
}
```

---

## 5. 运行时如何注入记忆

运行 Agent 时，Prompt Context 按以下顺序拼装：

```text
1. Agent Markdown 角色说明书
2. StoryWorldState
3. CandidateDraft / StoryEventFrame
4. AgentMemory 中与当前平台/题材匹配的 learned_patterns
5. 本轮 Message Bus 中相关消息
6. 输出 Schema 要求
```

注意：

- 不要把完整记忆文件全部塞进 prompt。
- 只取与当前 `genre`、`platform_type`、`chapter_position` 匹配的 Top K 记忆。
- 每条记忆必须带来源和置信度。

---

## 6. 记忆防污染机制

### 6.1 不直接用模拟结果更新长期记忆

模拟结果只能进入：

```text
Simulation Trace
```

不能直接进入：

```text
AgentMemory.learned_patterns
```

原因：

> 模型自己的判断如果反复写回，会形成自我强化，而不一定更接近真实市场。

---

### 6.2 真实反馈优先

长期记忆的主要来源应该是：

```text
真实反馈
人工确认
多次模拟一致结论
```

优先级：

```text
real_feedback > manual > repeated_simulation > single_simulation
```

---

### 6.3 所有记忆必须可追溯

每条 learned pattern 必须包含：

- 来源。
- 项目 ID。
- 创建时间。
- 置信度。
- 是否人工确认。
- 适用平台和题材。

---

### 6.4 低置信度记忆只作为提示

低置信度记忆只能影响解释，不应直接改变评分。

建议：

```text
confidence >= 0.75：可参与评分调整
0.50 <= confidence < 0.75：只作为提示
confidence < 0.50：不注入运行上下文
```

---

## 7. 文件结构建议

```text
script simulation/
  agents_md/
    audience_shuangwen.md
    audience_emotion.md
    audience_suspense.md
    audience_short_drama.md
    audience_paid_unlock.md
    audience_quality.md
    platform_editor.md
    platform_distribution.md
    writer.md
    judge.md
    report_agent.md
  storage/
    agent_memory/
      audience_shuangwen.json
      audience_emotion.json
      audience_suspense.json
      audience_short_drama.json
      audience_paid_unlock.json
      audience_quality.json
      platform_editor.json
      platform_distribution.json
      writer.json
      judge.json
    feedback/
    traces/
  backend/
    memory/
      memory_store.py
      memory_selector.py
      memory_update_service.py
```

---

## 8. 第一阶段实现范围

P0 不需要做复杂自动学习，但要把接口和文件结构打好。

第一阶段建议实现：

1. 每个 Agent 一个 Markdown 角色说明书。
2. 每个 Agent 一个空的 memory JSON。
3. 运行时读取 Agent memory，但只注入 Top K。
4. Trace 保存每次 Agent 输出。
5. 提供 `GET /memory` 和 `POST /memory/patterns`。

暂不做：

- 自动从模拟结果更新长期记忆。
- 复杂向量检索记忆。
- 全自动权重校准。
- 跨项目自动学习。

---

## 9. 与商业化的关系

Agent Memory 是未来商业化的重要资产。

对个人作者：

- 系统逐渐记住这个作者作品的读者反馈规律。
- 系统能发现作者常犯的问题。
- 系统能给出更贴近该作品的改稿建议。

对平台/机构：

- 每个平台可拥有自己的 Agent Memory。
- 不同题材、不同付费节点可以形成专属经验。
- 长期积累后形成私有“内容评估模型”。

商业化表达：

> 每个 Agent 都不是一次性评委，而是一个会被真实数据持续训练的虚拟读者/编辑/推流角色。

---

## 10. 结论

每个 Agent 应该有自己的记忆文档，并通过接口接收实时数据反馈。

但关键是：

> **记忆可更新，不等于记忆可无审计地自动污染。**

推荐做法：

```text
Markdown 角色说明书保持稳定
Agent Memory 记录可更新经验
Simulation Trace 保存每次判断
Real Feedback 负责校准
人工/规则审核后再写入长期记忆
```

这样系统既能从真实数据中进化，又不会因为模型自我强化而失真。
