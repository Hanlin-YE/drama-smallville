# Round 2 只选 key_agents 的理由

## 上下文

`audience_agents.py:run_round_two` 在环境摘要生成后，只让 6 个 key_agents 做修订判断，不是全部 Persona。`key_agents = {"audience_paid_unlock", "platform_distribution", "audience_emotion", "paid_unlock", "platform_feed", "emotion_immersive"}`。

被排除的是 `audience_shuangwen`（爽点追更型）和 `quality_keeper`（品质口碑型）。

## 决定

Round 2 只选 6 个 key_agents，排除爽点追更型和品质口碑型。

## 理由

1. **环境摘要影响的差异化**：Round 2 的修订逻辑是读 `env.recommendation_boost` / `env.controversy` / `env.comment_velocity` 后微调。这些环境信号对"付费解锁型"和"平台推流型"影响最大——它们的行为直接受平台推荐信号驱动。爽点追更型的判断主要靠"有没有打脸/反杀"（内容驱动，不是环境驱动），环境变化对它影响小。
2. **避免噪声**：让所有 Persona 都微调会产生过多小幅变动，淹没真正有意义的修正。少而精的修订更能体现"环境反馈影响判断"这个产品卖点。
3. **性能**：Round 2 的 Persona 数减半，O(Persona×Draft) 矩阵缩小一半。

## 被排除的 Persona 的理由

- **爽点追更型**：判断几乎完全由"有没有反杀/打脸/强冲突"决定，这是内容属性不是环境属性。环境摘要不会改变它对爽点的判断。
- **品质口碑型**：判断由逻辑一致性、人设合理性决定，也不受环境信号影响。

## 后果

- Round 2 修订覆盖面有限——只有 6/8 个 Persona 会修订。如果未来发现爽点追更型也受"评论区争议氛围"影响，需重新纳入。
- `key_agents` 集合同时包含新旧两套命名（`audience_paid_unlock` + `paid_unlock`），因为 KMeans 压缩后的 archetype 命名与 P0 硬编码命名不同。P1 统一命名后应清理。
