# MiroFish 架构借鉴与剧情模拟产品 PRD

> 日期：2026-06-13  
> 目标：分析 MiroFish 多 Agent 编排架构相对当前网文/短剧情节模拟 MVP 的优势，明确哪些设计可以吸收，哪些不适合直接照搬，并沉淀为后续产品和技术演进路线。  
> 当前产品方向：网文/短剧情节发展模拟引擎，让 LLM 扮演读者、观众、平台编辑和推流机制，对候选剧情分支进行留存、好评、付费和平台推荐潜力评估。

---

## 1. 背景

当前项目已经从“新品发布舆情推演”转向：

> **网文/短剧情节模拟引擎。**

核心问题是：

> 作者不知道下一步剧情如何发展时，能否先让一组 AI 读者/观众/平台 Agent 进行模拟反馈，帮助判断哪个分支更能提升留存、好评、付费和平台推荐潜力？

MiroFish 是一个开源的通用多 Agent 社会模拟项目。它的优势不在于自带模型，而在于提供了一套从 seed material 到世界建模、Agent 生成、互动模拟、状态保存和报告输出的通用编排思路。

本 PRD 的目标不是决定是否直接集成 MiroFish，而是回答：

1. MiroFish 的编排架构比当前 MVP 强在哪里？
2. 哪些设计应该立即借鉴？
3. 哪些设计适合后续阶段再做？
4. 哪些部分不适合当前产品直接照搬？
5. 如何把这些能力转化为我们的商业化路径？

---

## 2. 我们与 MiroFish 的定位差异

| 维度 | MiroFish | 我们 |
|---|---|---|
| 产品定位 | 通用多 Agent 社会模拟 / 预测引擎 | 网文/短剧情节分支测试 |
| 输入 | 新闻、政策、报告、现实材料等 seed material | 当前剧情、角色设定、前文剧情、候选下一步情节 |
| Agent | 大量泛化社会 Agent | 读者、观众、平台编辑、平台推流 Agent |
| 模拟环境 | 类 Twitter / Reddit 的社交互动场 | 评论区、弹幕、书评区、短剧付费节点、平台推荐机制 |
| 输出 | 通用预测报告 / 模拟结果 | 留存、好评、付费、平台推荐潜力、改写建议 |
| 价值主张 | 模拟现实世界事件如何演化 | 帮助创作者选择下一步剧情 |
| 商业闭环 | 通用研究/预测场景 | 创作测试、平台投放、剧本优化、IP 评估 |

一句话差异：

> **MiroFish 模拟世界，我们模拟剧情消费反馈。**

---

## 3. MiroFish 编排架构的优势

### 3.1 Seed Material 到 World Model 的流程更完整

MiroFish 不是直接让 Agent 对输入文本打分，而是先从 seed material 中抽取实体、关系、背景和冲突，再构建一个可模拟的世界状态。

这比当前 MVP 的：

```text
剧情输入 -> Agent 打分
```

更接近真正的仿真系统。

对我们的启发：

```text
当前剧情材料
-> StoryWorldState
-> Agent 评价
```

而不是直接把原始剧情塞给每个 Agent。

---

### 3.2 Agent 规模和人群模拟能力更强

MiroFish 强调生成大量具有独立人格、记忆和行为逻辑的 Agent，让它们自由互动，观察群体行为涌现。

当前 MVP 是：

```text
6 个读者/观众 Agent + 2 个平台侧 Agent
```

更像专家评审团。

MiroFish 的思路更像：

```text
构建一个小型社会样本
-> 让不同人群交互
-> 观察意见变化
```

对我们的启发：

后续可以从固定 8 个 Agent 扩展到：

- 核心粉丝。
- 路人观众。
- 付费用户。
- 逻辑党。
- 情绪党。
- 平台偏好人群。
- 黑粉/吐槽用户。
- 剧评型用户。

---

### 3.3 有社交平台式交互环境

MiroFish 不只是让 Agent 输出单轮评分，而是模拟社交平台中的发帖、回复、点赞、争论和关注关系。

对我们的启发：

我们不应该照搬 Twitter / Reddit，而是改造为内容消费场景：

```text
书评区
弹幕区
评论区
催更区
短剧付费卡点
章节末尾评论
```

Agent 不仅判断“我喜不喜欢”，还可以模拟：

- 会不会评论。
- 会不会催更。
- 会不会吐槽。
- 会不会推荐给朋友。
- 会不会付费解锁下一集。
- 会不会因为评论区争议改变判断。

---

### 3.4 记忆与 GraphRAG 思路更成熟

MiroFish 有知识图谱、记忆管理和 GraphRAG 方向的设计。

当前 MVP 还只是静态画像和 Markdown Agent。

对我们的启发：

后续剧情模拟应引入：

- 角色长期记忆。
- 世界观设定图谱。
- 人物关系图谱。
- 伏笔和未解悬念图谱。
- 爆款网文/短剧案例库。
- 平台反馈历史。

这能让系统从“单次评价”升级为“长期创作工作台”。

---

### 3.5 仿真过程更可观测

MiroFish 有 simulation lifecycle、state files、progress files、trace 和 reports 等结构。

这点对我们的产品非常重要。

剧情模拟不是一次 LLM 生成，而应该保存：

```text
输入剧情
StoryWorldState
Agent 输出
Agent 分歧
平台侧判断
权重配置
聚合过程
最终报告
```

这样才能复盘、调试、校准和商业化。

---

### 3.6 报告生成与模拟过程分离

MiroFish 将模拟过程和最终报告生成拆开。

我们也应该遵守这个边界：

```text
Audience / Platform Agents -> raw judgments
Weighted Judge -> score aggregation
Report Agent -> human-readable report
```

不能让每个 Agent 直接写最终报告，否则输出会发散，前端也难以展示。

---

### 3.7 异步任务管理适合长模拟

MiroFish 支持异步任务和进度管理，适合较长时间运行的多 Agent 仿真。

我们的 MVP 可以同步跑，但后续如果加入：

- 多轮辩论。
- 评论区模拟。
- 真实案例 RAG。
- 多章节连续推演。
- 大量观众 Agent。

就需要：

```text
POST /simulation/start
GET /simulation/{id}/status
GET /simulation/{id}/result
```

---

## 4. 可借鉴清单

### 4.1 P0：当前 MVP 就该借鉴

#### 1. StoryWorldState

在 Agent 评价前，先从剧情材料中抽取结构化世界状态。

建议字段：

```text
characters
relationships
current_conflict
unresolved_hooks
emotional_debts
power_dynamics
hidden_information
platform_context
chapter_position
```

价值：

- 让每个 Agent 看到一致的剧情理解。
- 减少不同 Agent 对原文理解不一致。
- 为后续图谱和长线剧情规划做准备。

---

#### 2. SimulationState

一次模拟应该有全局状态，而不是一堆函数临时变量。

建议字段：

```text
simulation_id
input
story_world_state
persona_weights
agent_judgments
platform_judgments
judge_summary
final_report
trace
```

价值：

- 支持调试。
- 支持复盘。
- 支持异步任务。
- 支持后续 replay。

---

#### 3. Agent Persona 独立配置

当前第一阶段使用 Markdown Agent 说明书，这个方向是对的。

建议目录：

```text
agents_md/
  audience_shuangwen.md
  audience_emotion.md
  audience_suspense.md
  audience_short_drama.md
  audience_paid_unlock.md
  audience_quality.md
  platform_editor.md
  platform_distribution.md
  judge.md
  report_agent.md
```

价值：

- 角色可编辑。
- 行为可复盘。
- 后续可扩展成画像库。
- 可从固定 Agent 演进到自动生成 Agent。

---

#### 4. Agent Trace

每个 Agent 的输入、输出、模型、prompt 版本都应保存。

建议保存：

```text
agent_name
prompt_file
prompt_version
model_id
input_hash
raw_output
validated_output
errors
latency
```

价值：

- 方便 debug。
- 支持复盘。
- 支持模型替换。
- 支持商业化审计。

---

#### 5. Report Agent

报告生成与评分聚合分离。

流程：

```text
Audience Agents
-> Weighted Judge
-> Report Agent
```

Report Agent 负责：

- 将 JSON 结果转为可读报告。
- 生成创作者可执行建议。
- 保留留存/好评/付费/平台推荐四类指标。

---

#### 6. OpenAI-compatible LLM Client

统一模型接口：

```text
base_url
api_key
model
```

价值：

- 可接云端模型。
- 可接本地模型。
- 可后续切换多模型。
- Agent 代码不依赖具体服务商。

---

### 4.2 P1：下一阶段借鉴

#### 7. Graph / Ontology 构建

把剧情材料抽成图：

```text
角色 -> 关系 -> 冲突 -> 目标 -> 隐瞒信息 -> 情绪债 -> 伏笔
```

应用场景：

- 悬疑。
- 复仇。
- 替身文学。
- 家族伦理。
- 身份揭露。
- 长线 IP。

---

#### 8. Agent Persona Generator

根据题材自动生成观众群，而不是永远固定 8 个 Agent。

示例：

```text
古装复仇短剧
-> 下沉爽感观众
-> 女性情感观众
-> 付费解锁观众
-> 平台推流 Agent

悬疑无限流
-> 推理读者
-> 设定党
-> 逻辑洁癖读者
-> 平台编辑 Agent
```

---

#### 9. 评论区/弹幕模拟

借鉴 MiroFish 的社交互动，但改造成内容平台反馈：

```text
评论区
弹幕
书评区
催更区
短剧评论区
```

输出：

- 模拟评论热词。
- 高赞评论。
- 吐槽点。
- 催更点。
- 争议点。

---

#### 10. Opinion Shift / 多轮演化

不只做一次评分，而是模拟意见变化：

```text
第一眼反应
-> 看完结尾钩子后的反应
-> 看到其他观众评论后的反应
-> 是否改变付费意愿
```

这会增强“涌现感”。

---

#### 11. 异步任务接口

当模拟时间超过 30 秒，需要支持：

```text
POST /simulation/start
GET /simulation/{id}/status
GET /simulation/{id}/result
```

---

### 4.3 P2：商业化阶段借鉴

#### 12. GraphRAG / Memory 系统

引入：

- 爆款案例库。
- 平台反馈历史。
- 用户自己的作品库。
- 角色长期记忆。
- 章节伏笔图谱。

---

#### 13. 大规模人群模拟

从 8 个 Agent 扩展到几十/几百个观众代理。

目标：

- 模拟群体分化。
- 模拟评论区意见感染。
- 模拟小圈层扩散。
- 模拟付费意愿分布。

---

#### 14. 多平台模拟

将平台环境从单一平台扩展为：

```text
番茄
起点
晋江
红袖
抖音短剧
快手短剧
微信小程序短剧
```

每个平台有不同：

- 内容偏好。
- 推荐机制。
- 付费模式。
- 用户口味。
- 审核风险。

---

#### 15. 可交互模拟世界

用户不仅看报告，还能追问：

```text
为什么情感读者不喜欢 B？
如果把男主误会提前解除会怎样？
平台编辑为什么不推荐 A？
付费用户为什么不愿意解锁？
```

---

## 5. 不建议现在直接照搬的部分

### 5.1 千级 Agent

对当前 MVP 太重。剧情测试先做 8-10 个高质量 Agent 更有效。

### 5.2 Twitter / Reddit 原样模拟

我们的场景不是公共社交媒体，而是：

```text
书评区
弹幕
评论区
付费卡点
平台推荐
```

### 5.3 通用预测定位

不能做成“预测任何剧情/任何市场”的泛工具。

必须保持垂直：

> **网文/短剧情节分支测试。**

### 5.4 强依赖外部重型组件

如 Zep Cloud、复杂 GraphRAG、外部仿真框架等，当前阶段会增加部署和调试成本。

### 5.5 AGPL 代码深度嵌入商业核心

MiroFish 是开源项目，但如果采用 AGPL 代码作为商业 SaaS 后端，需要谨慎处理许可证边界。

建议：

- 可研究。
- 可实验。
- 可做隔离适配。
- 商业化核心尽量保持自研或明确合规。

---

## 6. 推荐产品架构

### 6.1 第一阶段：本地 Markdown Agent 引擎

```text
Raw Story Input
-> Story Parser
-> StoryWorldState
-> Markdown Agent Evaluation
-> Platform Agent Evaluation
-> Weighted Judge
-> Report Agent
-> StorySimulationReport
```

目标：

- 能跑通。
- 能路演。
- 能展示留存/好评/付费/平台推荐四类输出。
- 能保存 trace。

---

### 6.2 第二阶段：世界状态与评论区模拟

```text
StoryWorldState
-> Agent Judgment
-> Comment Zone Simulation
-> Opinion Shift
-> Revised Judge
```

目标：

- 模拟评论区反馈。
- 模拟观点变化。
- 体现更强的群体涌现。

---

### 6.3 第三阶段：案例库和 GraphRAG

```text
StoryWorldState
-> Similar Case Retrieval
-> Persona Agent Evaluation
-> Case-informed Judge
```

目标：

- 引入爆款作品案例。
- 提升可信度。
- 为商业化做数据壁垒。

---

### 6.4 第四阶段：真实数据复盘

```text
Prediction
-> Real Feedback Data
-> Gap Analysis
-> Calibration
-> Case Memory Update
```

目标：

- 接入完读率、追更率、评论关键词、付费转化。
- 做预测 vs 实际复盘。
- 持续校准平台权重和 Agent 行为。

---

## 7. 推荐技术模块清单

### P0 模块

| 模块 | 作用 |
|---|---|
| StoryWorldState Builder | 从剧情材料抽取角色、关系、冲突、伏笔、情绪债 |
| SimulationState | 保存一次模拟的全局状态 |
| Markdown Agent Engine | 读取 Agent md 文件并调用 LLM |
| Agent Trace Store | 保存每个 Agent 的输入输出和错误 |
| Weighted Judge | 加权聚合留存、好评、付费、平台推荐 |
| Report Agent | 生成可读报告 |
| LLM Client | 统一模型调用 |

### P1 模块

| 模块 | 作用 |
|---|---|
| Comment Zone Simulator | 模拟评论区/弹幕/书评区 |
| Opinion Shift Engine | 模拟观点被其他评论影响后的变化 |
| Persona Generator | 按题材自动生成 Agent |
| Async Simulation API | 支持长任务状态查询 |

### P2 模块

| 模块 | 作用 |
|---|---|
| GraphRAG Adapter | 接入角色关系、伏笔和历史案例图谱 |
| Case Memory Store | 存储爆款案例和用户私有案例 |
| Real Feedback Importer | 导入真实完读、付费、评论数据 |
| Calibration Engine | 根据真实数据校准权重和评分 |

---

## 8. 路演差异化表达

可以这样表达：

> MiroFish 证明了多 Agent 可以模拟社会反馈，但它是通用预测引擎。我们把这个思想垂直落到网文和短剧创作：不是模拟整个世界，而是模拟“读者、观众、平台编辑和推荐系统”会如何看待下一步剧情。

更短的版本：

> **MiroFish 模拟社会，我们模拟观众席和平台分发。**

---

## 9. 当前结论

MiroFish 的优势是：

- 世界构建。
- 群体模拟。
- 社交互动。
- 记忆/图谱。
- 异步仿真。
- 报告流水线。

我们应该吸收它的仿真工程结构，但不照搬它的通用预测定位。

当前最该立刻落地的是：

1. 先构建 `StoryWorldState`，再让 Agent 评价。
2. 保存完整 `SimulationState` 和 `Agent Trace`。
3. 将 `Report Agent` 从 `Weighted Judge` 中拆出来。
4. 保持 OpenAI-compatible LLM Client。
5. 预留后续 GraphRAG、评论区模拟和异步任务接口。

最终产品应形成自己的核心资产：

> **垂直剧情 Agent、平台权重、StoryWorldState、爆款案例库、真实反馈复盘和创作改写建议。**
