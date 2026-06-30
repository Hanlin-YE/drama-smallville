# ScriptMind 不可达时的降级策略

## 上下文

ADR-0001 决定 ScriptMind 作为工具层。但 ScriptMind 是外部服务，会挂、会超时、会返回 500。剧组各 Role 调它失败时怎么办？

有三个选项：
- **A. 快速失败**：ScriptMind 挂了就报错，demo 崩。
- **B. 降级到规则引擎**：每个 Role 有 rule-based fallback，失败时自动切换。
- **C. 队列重试**：失败后入队重试，等 ScriptMind 恢复。

## 决定

采用 **B：降级到规则引擎**。每个 Role（编剧、剧本医生）都有 rule-based fallback，ScriptMind 不可达时自动切换，demo 不崩。

## 理由

1. demo 稳定性 > LLM 真实性。P0 阶段路演时 ScriptMind 挂了不能让整个系统停摆。
2. 规则引擎已存在（writer 的 `_generate_rule_based`、creative_advisors 的纯规则评审），降级路径零开发成本。
3. ScriptMind 恢复后自动切回 LLM（每次调用都 try ScriptMind 先），无需手动恢复。
4. 队列重试（C）对 P0 太重，且短剧试播是同步交互，不适合异步队列。

## 后果

- 降级时输出质量下降（规则 vs LLM），但结构不变。报告中已声明"P0 权重为启发式"。
- 需要在日志中明确记录"降级到 rule-based"，方便事后排查。已在 writer.py 和 creative_advisors.py 用 `logger.warning/info` 实现。
- 2026-06-29 验证：ScriptMind `/api/plan` 500 时 writer 降级到 rule-based，`/api/extract-features` 400 时剧本医生降级到纯规则——降级路径已实测通过。
