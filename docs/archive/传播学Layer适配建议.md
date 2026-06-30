# 传播学 Layer 对网文/短剧情节模拟的适配建议

> 日期：2026-06-13  
> 来源参考：`群众行为Agent模拟层PRD v3 - 传播学融合版`  
> 目标：判断该 PRD 中的 layer 分层哪些可以用于当前 `script simulation` 项目，并转译为网文/短剧情节模拟的技术模块。

---

## 1. 总体判断

这份 PRD 需要**批判性吸收**。它最有价值的部分不是“大规模 OASIS 接入”，也不是把所有传播学模型都工程化，而是它把多 Agent 从“发表观点”升级为：

```text
事件刺激
-> 需求满足
-> 框架解读
-> 状态变化
-> 行为阈值
-> 社交传播
-> 平台分发
-> 聚合报告
```

这正好能补强我们当前的网文/短剧情节模拟。我们现在的 MVP 是：

```text
当前剧情 + 候选分支
-> 读者/观众/平台 Agent 评分
-> 加权聚合
-> 留存、好评、付费、平台推荐预测
```

建议吸收为一个轻量参考框架：

```text
当前剧情 + 候选分支
-> Story Event Layer
-> Need Layer
-> Framing Layer
-> State Update Layer
-> Behavior Threshold Layer
-> Platform Feed Layer
-> Report Layer
```

第一阶段不需要完整实现社交传播和 OASIS，也不应该让理论模型凌驾于产品目标之上。传播学模型在当前产品中应作为：

```text
Agent 交互与评分的参考框架
```

而不是：

```text
必须严格执行的硬仿真公式
```

原因：

1. 网文/短剧创作是强类型、强套路、强平台约束的内容生产问题，不是标准公共舆论扩散问题。
2. 传播学模型可以帮助解释“为什么继续看/评论/付费”，但不能替代剧情节奏、爽点、人物关系和平台商业逻辑。
3. MVP 需要稳定、可解释、可路演，而不是理论最完整。
4. 过度模型化会让系统变重，反而削弱“作者改稿建议”的直接价值。

因此当前策略是：

```text
轻量采用：Need / Frame / State / Threshold
谨慎采用：Social Propagation / Opinion Dynamics
暂不采用：完整 OASIS 大规模仿真
```

---

## 1.1 OASIS 接入边界

如果后续接入 OASIS，本质上确实会变成“调用外部仿真引擎”，也会重新走适配层路线。

因此 OASIS 不能成为第一阶段主路径，只能作为高级模式：

```text
默认模式：Local Light Simulator
高级模式：OASIS Adapter
```

两者必须通过统一接口隔离：

```python
class SimulationEngine:
    def run(input: StorySimulationInput) -> StorySimulationReport:
        ...
```

第一阶段：

```text
SimulationEngine = LocalLightSimulator
```

后续可选：

```text
SimulationEngine = OasisAdapter
```

### OASIS 可能带来的风险

| 风险 | 说明 | 应对 |
|---|---|---|
| 集成复杂度 | 需要把我们的剧情事件、Agent 画像、行为概率映射到 OASIS 输入 | 先做导出 JSON，不自动运行 |
| 输出不匹配 | OASIS 输出偏社交传播，未必直接对应留存/好评/付费 | 做 mapped_metrics 转换层 |
| 成本和性能 | 大规模 Agent 仿真会慢，可能不适合实时产品体验 | 仅作为离线高级实验 |
| 产品焦点偏移 | 容易从“剧情改稿工具”变成“仿真平台” | 默认主流程仍是剧情建议 |
| 许可证/依赖风险 | 外部开源组件可能影响部署和商业化 | 适配层隔离，商业化前审查 |
| 可解释性风险 | 大规模仿真结果如果无法解释，用户难以信任 | 保留 Light Simulator 的规则解释 |

### 推荐接入阶段

P0：

- 不接 OASIS。
- 只保留 `OasisAdapter` 目录和接口设计。
- 确保 Light Simulator 可独立完成 MVP。

P1：

- 支持导出 OASIS 输入 JSON。
- 支持手动运行 OASIS 后导入结果。
- 不在产品主流程自动调用。

P2：

- 后台异步调用 OASIS。
- 前端展示“高级传播仿真结果”。
- 和 Light Simulator 结果并排比较。

P3：

- 商业化高级版支持大规模观众群仿真、多平台传播网络和推荐系统参数调节。

一句话原则：

> **OASIS 是实验室，不是发动机舱。**

我们的主引擎仍然应该是垂直剧情 Light Simulator。OASIS 只用于高级传播实验，不应绑死核心业务链路。

---

## 2. 可采用的 Layer

### 2.1 Input Layer

可以直接采用。

我们对应的输入是：

- 当前剧情。
- 前文剧情。
- 角色设定。
- 当前冲突。
- 平台类型。
- 章节位置。
- 候选下一步情节。
- 业务目标：留存、好评、付费、平台推荐。

对应现有 Schema：

```text
StorySimulationInput
CandidatePlot
```

建议新增：

```text
raw_story_material
target_platform_rules
chapter_context
```

---

### 2.2 Event Layer

非常值得采用。

当前我们不应该直接把候选剧情丢给 Agent，而应该先把每个候选剧情转成 `StoryEventFrame`。

建议字段：

```python
class StoryEventFrame(BaseModel):
    event_id: str
    candidate_plot_id: str
    episode: int | None
    chapter: int | None
    scene: int | None
    description: str
    tags: list[str]
    intensity: float
    hook_value: float
    cliche_risk: float
    paywall_value: float
    compliance_risk: float
    logic_risk: float
    emotion_value: float
    novelty_value: float
    agenda_topics: list[str]
    meme_potential: float
    controversy_potential: float
```

这比只用 `CandidatePlot.summary` 更适合计算。

MVP 中可先由 LLM Parser 生成这些字段，后续再加规则校准。

---

### 2.3 Need Layer

必须采用，P0。

对应传播学中的 Uses and Gratifications。

短剧/网文读者的需求可以定义为：

```text
emotional_release
face_slapping_satisfaction
revenge_fantasy
romance_tension
curiosity_resolution
social_talk
identity_projection
aesthetic_quality
logic_satisfaction
payoff_expectation
```

每个 Agent 画像里应该有：

```python
gratification_needs: dict[str, float]
```

计算：

```text
need_match_score = sum(event_tag_weight * agent_need_weight)
```

它决定：

- attention。
- curiosity。
- emotion。
- retention。
- pay_intent。
- comment_intent。

---

### 2.4 Framing Layer

必须采用，P0。

同一剧情，不同读者会用不同框架理解：

```text
爽点读者：这是反杀前的压迫铺垫吗？
情感读者：这段关系拉扯是否成立？
悬疑读者：线索是否公平？
平台编辑：这个卖点是否可推荐？
平台推流：这个开场能否带来完播？
```

每个 Agent 画像里应有：

```python
interpretation_frame: str
frame_weights: dict[str, float]
```

计算：

```text
frame_match_score = sum(agent.frame_weights[event_tag])
```

正向匹配提升：

- attention。
- emotion。
- curiosity。
- pay_intent。

负向匹配提升：

- irritation。
- drop_off_risk。
- counter_intent。
- negative_review_risk。

---

### 2.5 State Update Layer

必须采用，P0。

我们现在的评分维度应该进一步拆成“状态变量”。

建议状态：

```python
class AudienceState(BaseModel):
    attention: float
    emotion: float
    curiosity: float
    trust: float
    irritation: float
    retention_intent: float
    positive_review_intent: float
    pay_intent: float
    comment_intent: float
    share_intent: float
    drop_off_risk: float
    platform_recommendation_fit: float
```

综合更新：

```text
state_delta =
  need_match_score
  + frame_match_score
  + preference_match_score
  + chapter_position_bonus
  + platform_fit_score
  + social_influence_score
```

MVP 可以先不做复杂社交影响，但要保留字段。

---

### 2.6 Behavior Threshold Layer

必须采用，P0。

这是把“感觉不错”变成可执行输出的关键。

短剧/网文场景行为：

```text
continue_reading
drop_off
pay_to_unlock
give_positive_review
comment
share
hate_watch
wait_for_recap
passive_watch
```

每个 Agent 画像应有：

```python
behavior_thresholds: dict[str, float]
```

行为概率：

```python
class BehaviorProbabilities(BaseModel):
    continue_reading: float
    give_positive_review: float
    pay_to_unlock: float
    comment: float
    share: float
    drop_off: float
    hate_watch: float
```

这些概率最终直接映射到我们的核心输出：

- 留存。
- 好评。
- 付费。
- 评论。
- 分享。
- 弃坑。

---

### 2.7 Platform Feed Layer

必须采用，但 P0 先做简化版。

对应我们已有的“平台推流 Agent”，但要从主观评价升级为状态计算。

建议平台状态：

```python
class PlatformState(BaseModel):
    heat: float
    completion_signal: float
    comment_velocity: float
    share_velocity: float
    paywall_signal: float
    controversy: float
    fatigue: float
    platform_amplification: float
```

推荐流影响公式可简化为：

```text
platform_amplification =
  completion_signal * 0.30
  + comment_velocity * 0.20
  + share_velocity * 0.20
  + paywall_signal * 0.20
  + controversy * 0.10
  - fatigue * 0.20
```

MVP 输出：

- 平台推荐潜力。
- 平台适配风险。
- 是否适合投流。
- 是否适合卡付费点。

---

### 2.8 Aggregation Report Layer

可以直接采用。

我们需要把 Agent 状态和行为概率汇总为：

```text
retention_prediction
positive_review_prediction
paid_conversion_prediction
platform_recommendation_prediction
drop_off_risk
comment_potential
share_potential
```

按权重聚合：

```text
metric = sum(agent_metric * segment_weight) / sum(segment_weight)
```

---

## 3. 暂缓采用的 Layer

### 3.1 Social Propagation Layer

有价值，但不适合第一阶段完整实现。

原因：

- 当前 MVP 重点是剧情分支选择，不是完整传播网络。
- 社交传播需要评论区、关系图和多时间步，工程量更大。

P0 可以只保留：

```text
comment_potential
share_potential
social_talk_score
```

P1 再模拟：

- 评论区高赞评论。
- 弹幕反应。
- 闺蜜群安利。
- 吐槽式传播。

---

### 3.2 Opinion Dynamics Layer

P1/P2 再做。

可后续引入：

- Two-Step Flow：高赞评论/短剧 KOL 影响普通观众。
- Linear Threshold：多人安利后触发付费。
- Spiral of Silence：少数意见被压制。
- Bounded Confidence：审美圈层分化。
- SIR / Rumor：梗和吐槽点传播生命周期。

当前 MVP 不需要完整实现，否则会拖慢路演。

---

### 3.3 OASIS Adapter

P2/P3 再考虑。

OASIS 适合大规模社交传播实验，但当前产品第一阶段更需要：

- 可控。
- 快速。
- 可解释。
- 能生成明确剧情建议。

因此当前只需保证数据结构未来可映射到 OASIS：

```text
AgentProfile
StoryEventFrame
BehaviorProbabilities
SocialEvent
PlatformState
```

---

## 4. 对当前 MVP 技术方案的具体修改建议

### 4.1 新增 StoryEventFrame

把候选剧情结构化成可计算事件。

文件建议：

```text
backend/schemas/event.py
```

---

### 4.2 新增 AgentProfile 完整结构

当前 `persona.py` 不应只存名称和权重，还应包含：

```text
gratification_needs
interpretation_frame
frame_weights
state
behavior_thresholds
social
model_policy
speaking_style
```

文件建议：

```text
backend/schemas/persona.py
```

---

### 4.3 新增 communication_models.py

实现：

```python
compute_need_match(agent, event)
compute_frame_match(agent, event)
compute_preference_match(agent, event)
```

---

### 4.4 新增 state_update_engine.py

实现：

```python
update_agent_state(agent, event, context)
apply_delta_and_clamp(state, delta)
```

---

### 4.5 新增 behavior_decision_engine.py

实现：

```python
decide_behavior(state, thresholds)
convert_behaviors_to_probabilities(state, thresholds)
```

---

### 4.6 新增 platform_feed_simulator.py

实现：

```python
compute_platform_amplification(platform_state)
estimate_recommendation_potential(agent_outputs, platform_context)
```

---

### 4.7 保留 Markdown Agent

Markdown Agent 不应被替代，而是从“直接评价”变成：

```text
解释计算结果 + 补充定性反馈 + 给出改写建议
```

也就是说：

```text
规则/传播学模型负责稳定计算
LLM Agent 负责解释、补充、改写建议
```

---

## 5. 推荐的新 P0 架构

```text
Raw Story Input
-> Story Parser Agent
-> StoryEventFrame Builder
-> AgentProfile Loader
-> Need Layer
-> Framing Layer
-> State Update Layer
-> Behavior Threshold Layer
-> Platform Feed Layer
-> Markdown Agent Explanation
-> Weighted Aggregation
-> Report Agent
```

最小可实现版本：

```text
1. 把 3 个候选剧情转成 StoryEventFrame
2. 读取 8 个 AgentProfile
3. 计算 need_match / frame_match
4. 更新 attention / emotion / retention / pay / drop_off 状态
5. 转成留存、好评、付费、平台推荐概率
6. LLM 生成每个 Agent 的理由和改写建议
7. Judge 聚合并输出推荐分支
```

---

## 6. 哪些最值得立刻用

按优先级排序：

1. **Event Layer**：把候选情节转成 `StoryEventFrame`。
2. **Need Layer**：按读者需求计算匹配度。
3. **Framing Layer**：按读者解释框架计算情绪和反感。
4. **State Update Layer**：把匹配度转成状态变化。
5. **Behavior Threshold Layer**：把状态转成留存、好评、付费、弃坑概率。
6. **Platform Feed Layer 简化版**：把完读、评论、付费信号转成平台推荐潜力。
7. **Aggregation Report Layer**：按权重汇总成报告。

---

## 7. 结论

这份传播学 PRD 对我们非常有价值，尤其是：

> **不要让 Agent 直接表态，而要让 Agent 通过需求、框架、状态和阈值产生行为。**

当前 MVP 应吸收它的计算链路，但保持实现轻量：

- P0 做 Light Simulator。
- P1 做评论区和意见演化。
- P2/P3 再考虑 OASIS 或大规模仿真。

最终产品差异化可以表达为：

> 我们不是让 AI 随便点评剧情，而是用传播学模型模拟不同观众为什么看、怎么看、状态如何变化，以及最终是否继续看、好评、付费或弃剧。
