# Drama Smallville — 短剧虚拟试播台

一个把短剧/网文剧情草稿送进虚拟观众群试播、收集反应、给出改稿建议的多 Agent 系统。剧组 Agent 集群负责生产内容，观众 Agent 集群负责产生反应，两个集群通过"试播"这个动作耦合。

## Language

### 两个集群（最顶层概念）

**剧组 (Production Crew)**:
生产短剧内容的 Role 集合，按真实剧组职位分工组织。现阶段最小集为 2 个 Role：编剧 + 剧本医生。分镜师经评估后砍掉（ScriptMind 工具层无分镜能力，且分镜与剧本是接力而非并行，违背多 Agent 并行设计目标）。
_Avoid_: writer agents, creative agents, "Agent"（裸用会与观众侧重载）

**观众群 (Audience Population)**:
依现实数据调参的 Persona 集合，每个 Persona 带权重，模拟复杂世界的观众反应分布。
_Avoid_: user agents, simulated users, "Agent"（裸用会与剧组侧重载）

### 集群内的个体

**Role**:
剧组里的一个职位，拥有自己的工作记忆和职责边界。调用 ScriptMind 完成其 LLM 工作。现阶段 2 个：
- **编剧 (Screenwriter)**：用户输入 + 创作意图 → 动态构造 ScriptMind `/api/plan` 请求 → 拿 3 套草稿。生产 Role。
- **剧本医生 (Script Doctor)**：对编剧的草稿调 ScriptMind `/api/generate` 拿改稿建议。审稿 Role。
_Avoid_: crew agent, production agent, "Agent"

**Persona**:
观众群里一个依真实数据拟合的观众原型，带 segment_weight 和行为阈值。由人口采样 + 聚类压缩产生，不是手工枚举。
_Avoid_: audience agent, user type, user persona（"user persona"是产品设计术语，这里是统计拟合产物）

### 并行点（多 Agent 并行合作的真正位置）

并行不靠剧组成员数量堆，而在以下三处：
1. ScriptMind `/api/plan` 一次返回 3 套草稿 = 3 个并行草稿产物
2. 剧本医生对 3 套草稿的审稿可 `asyncio.gather` 并行
3. 观众群多 Persona × 多 Draft 的 Judgment 是 O(Persona×Draft) 并行矩阵

### 核心动作

**试播 (Pilot)**:
把一个 Draft 送进观众群，收集所有 Persona 的 Judgment，产出一份 PilotReport。一个 Draft 可以多次试播（round_1 → round_2）。
_Avoid_: simulation（太泛）, run（太泛）

**Draft**:
编剧产出的剧情草稿，是试播的输入单位。
_Avoid_: candidate, plan output

**Judgment**:
一个 Persona 对一个 Draft 在某一轮的反应，含 continue/pay/comment/share/dropoff 六个维度。
_Avoid_: score, rating, response

### 工具层

**ScriptMind**:
外部工具层，提供 LLM 驱动的 /api/plan（生成剧本大纲）、/api/generate（文案与改稿建议）、/api/extract-features（语义特征提取）。Role 调用它完成 LLM 工作，不自建 LLM Key。请求参数根据用户输入文本动态构造，不写死（见 ADR-0001）。
_Avoid_: LLM gateway（太泛）, the API, scriptmind service

### 状态

**工作记忆 (Working Memory)**:
单个 Role 或 Persona 跨试播轮次保留的状态——观察到的模式、校准备注、置信度。每个 Role 的工作记忆由其职责决定，针对性设计，不共享通用 schema。接入主流程（不再是死代码）。
_Avoid_: memory store, agent memory（太泛）, cache

## 已砍掉的（不要重新捡起来）

- **分镜师**：ScriptMind 无分镜端点；分镜与剧本是接力非并行；优先级低于故事大纲和剧本。见上"剧组"定义。
- **品牌舆情推演方向**：已归档至 docs/品牌舆情推演_已归档.md。本项目只做短剧试播。

## 待定术语（还没吵清楚，不要急着用）

- Persona 的 confidence 算法（当前硬编码 0.72，待用真实数据替换）
- 剧本医生工作记忆的具体 schema（方向3，待 LLM 调通后设计）
