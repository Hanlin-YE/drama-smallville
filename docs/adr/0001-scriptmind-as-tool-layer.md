# ScriptMind 作为工具层（不自建 LLM Key）

## 上下文

剧组各 Role 需要 LLM 能力（生成剧本大纲、改稿建议、语义特征提取）。有两条路：

- **路线 A**：每个 Role 自己调 DeepSeek API，需要自建 LLM Key、自管 prompt、自管重试。
- **路线 B**：Role 调 ScriptMind 已有的端点（/api/plan、/api/generate、/api/extract-features），ScriptMind 内部用 DeepSeek v3.1 完成 LLM 工作，Role 拿结构化结果继续处理。

## 决定

采用**路线 B**：ScriptMind 作为工具层，Role 不自建 LLM Key。

## 理由

1. ScriptMind 已经实现了三个端点背后的 LLM prompt 工程，Role 重复造轮子没有杠杆。
2. 不自建 Key 意味着不需要管理密钥轮转、配额、计费——P0 阶段这些是噪音。
3. Role 的请求参数根据用户输入文本**动态构造**，不写死 JSON——这保留了 Role 对 ScriptMind 调用的控制权，工具层只提供能力不提供数据。

## 后果

- ScriptMind 成为单点依赖；它挂了剧组就停摆。需要 fallback 策略（见 ADR-0002 待写）。
- Role 的 prompt 工程权交给了 ScriptMind；如果某个 Role 需要 ScriptMind 没有的 LLM 能力，要么提需求给 ScriptMind，要么这条路要重新评估。
- 动态构造请求参数意味着 Role 需要一个"把用户输入 + 工作记忆 → ScriptMind 请求体"的映射层，这不是透传。
