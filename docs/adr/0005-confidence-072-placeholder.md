# 0.72 这个反复出现的魔法阈值

## 上下文

代码里 `0.72` 这个数字在 4 处出现,语义各不相同但彼此关联:

1. `agents/audience_agents.py:97` — `AudienceJudgment.confidence=0.72`,每个观众判断的置信度,写死在 `_judge_draft` 返回值里。
2. `agents/judge.py:66` — `confidence_level` 分档阈值:`>= 0.72` 为 high,`>= 0.52` 为 medium,否则 low。0.72 既是置信度本身又是 high 档下沿。
3. `agents/script_doctor.py:23` — `paid_conversion_score > 0.72 and logic_consistency_score < 0.70` 作为"商业强但逻辑弱"的预警条件。
4. `simulation/quality_evaluator.py:34` — `creative_continuity` 评分缺失时的兜底值 `or [0.72]`。

## 决定

把 0.72 记为 **P0 阶段的启发式占位值**,不现在抽出常量,等 P1 用真实数据替换。

## 理由

1. **来源是经验拍脑袋,不是数据拟合**。P0 没有 CalibrationRecord 管线(PRD §3.4 待办),0.72 是"看起来合理的中偏高置信度"的占位,目的是让管线跑通、能产出可读报告,而不是精确校准。
2. **三处语义同源**:judge 的 high 阈值、script_doctor 的预警线、audience_agents 的置信度——都指向"这个判断/这个草稿足够可信"。用同一个 0.72 是有意为之的耦合,不是巧合。quality_evaluator 的兜底值是另一层语义(创意连续性的中性默认),但碰巧同值。
3. **现在抽常量是过早抽象**。这三个位置的未来去向不同:audience_agents 的 confidence 应该由真实观众反馈校准;judge 的阈值应该由 confidence_score 的分布决定;script_doctor 的预警线应该由业务方定义可接受的风险偏好。现在用一个 `CONFIDENCE_HIGH = 0.72` 常量把它们绑死,反而阻碍各自独立校准。
4. **CONTEXT.md 已标"待定"**:`confidence = 0.72` 列在待定术语里,本文档补充它的来源与替换计划。

## 后果

- 0.72 保持散落各处,直到 P1 引入真实反馈数据。
- P1 替换清单:
  - `audience_agents.py:97` → 由 CalibrationRecord 反推每个 archetype 的置信度
  - `judge.py:66` → 用 confidence_score 实际分布的某分位数(如 P75)定义 high
  - `script_doctor.py:23` → 业务方可配置的风险阈值
  - `quality_evaluator.py:34` → 用历史 creative_continuity 均值兜底,而非硬编码
- 替换时务必同步检查 trace 回放:历史 trace 里 `confidence: 0.72` 满地都是,改阈值后旧 trace 的 `confidence_level` 会与新逻辑不一致——回放对比时需注意这是版本差异不是 bug。
