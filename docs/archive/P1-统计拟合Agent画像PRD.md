# Drama Smallville P1 PRD：统计拟合 Agent 画像与商业化骨架

> 日期：2026-06-14  
> 目标：在 P0 可运行闭环基础上，引入“真实宏观数据 -> 数学分布 -> 少量代表 Agent”的统计拟合机制；同时建立商业化架构边界，使后续接真实反馈、RAG、OASIS-like 社交网络仿真时不推倒重来。  
> 核心原则：架构层按商业化终局设计，实现层按 P1 最小能力打开。

---

## 1. 一句话定位

P1 不再只依靠手写人设和固定权重，而是用真实宏观数据约束虚拟观众群体的生成。

系统用公开行业统计和后续真实反馈，拟合出 **个位数级别的代表性 Agent**，使它们的加权组合在年龄、观看频率、付费倾向、评论倾向、平台偏好等宏观特征上接近真实用户总体。

P1 的工程原则是：

> **能调参解决的，不新增 Agent。**

也就是说，优先通过权重、阈值、分布参数、平台 multiplier、题材 multiplier、business goal multiplier 来拟合真实世界，而不是不断增加 Agent 数量。

---

## 2. 开源项目借鉴结论

### 2.1 Agent4Rec

Agent4Rec 是推荐系统用户模拟方向的代表项目。它用 1000 个 LLM generative agents 模拟推荐系统用户，这些 Agent 从 MovieLens-1M 数据集初始化，具备不同社会特征和偏好，并在推荐页面中执行观看、评分、评价、退出、访谈等动作。

对我们的启发：

```text
Agent 不应完全靠 prompt 想象。
Agent Profile 应从真实数据或统计分布初始化。
Agent 动作必须结构化。
模拟结果需要和真实行为对齐。
```

### 2.2 RecAgent

RecAgent 将系统拆成 user module 和 recommender module。用户 Agent 可以浏览推荐网站、与其他用户交流、在社交媒体广播消息。

对我们的启发：

```text
观众 Agent 和平台推荐模块必须分离。
用户行为不只是评分，还包括浏览、评论、分享、退出。
```

### 2.3 OASIS

OASIS 将社交仿真拆成 platform、agents、actions、recommendation system、simulation engine。它面向 Twitter / Reddit 风格社交平台，支持大规模 Agent、动态社交网络和推荐流。

对我们的启发：

```text
我们应复刻 OASIS 的抽象：AgentProfile、ActionSpace、Environment、FeedSimulator、TraceLog。
但不照搬 Twitter/Reddit 场景，也不在 P1 接原生 OASIS。
```

### 2.4 对 P1 的结论

P1 不是做完整商业化功能，而是建立商业化骨架：

```text
React/Vite 前端骨架
FastAPI 后端
统计拟合 Agent Population
Evidence-based Agent Memory
LightSocialSimulator
FeedSimulator
Trace / History
```

---

## 2.5 P1 明确实现框架

P1 不是 P0 的简单 UI 包装，也不是完整商业化系统。它要实现一个商业化骨架版：

```text
React/Vite Frontend
-> FastAPI Backend
-> Audience Research Config
-> Population Sampler
-> Representative Agent Compressor
-> Population Fit Validator
-> AgentProfileSet Loader
-> LightSocialSimulator
-> FeedSimulator
-> CommentSimulator
-> Evidence-based Agent Memory
-> Trace History
```

P1 主链路：

```text
用户输入剧情
-> 选择平台/目标
-> 加载 audience_research.yaml
-> 采样 synthetic audience
-> 压缩为 4-7 个代表 Agent
-> 校验拟合误差
-> 用代表 Agent 运行虚拟试播
-> 输出推荐、评分、模拟评论、拟合报告
```

P1 必须实现：

- React/Vite 基础前端。
- `audience_research.yaml`。
- 4-7 个代表 Agent。
- PopulationFitReport。
- CommentSimulator。
- Trace History。
- Evidence-based Memory 读写。

P1 可以暂缓：

- 自动真实数据校准。
- 复杂聚类算法。
- 原生 OASIS。
- 多模型 UI。
- 登录和权限。

---

## 3. 为什么要用数学分布

真实世界给我们的不是一个个具体 Agent，而是统计约束：

```text
年龄分布
观看频率分布
复看比例
付费倾向
评论倾向
分享倾向
题材偏好
平台偏好
```

所以正确做法是：

```text
宏观统计
-> 参数化分布
-> 抽样生成虚拟观众 population
-> 用少量代表 Agent 近似该 population
-> 校验代表 Agent 的加权组合是否匹配宏观分布
```

这比直接手写：

```text
爽点观众 0.25
付费观众 0.30
```

更严肃，也更利于后续真实数据校准。

---

## 4. 四层真实画像体系

### 4.1 行业级画像

来源：

- 网络文学行业报告。
- 微短剧行业白皮书。
- 网络视听发展报告。

用途：

- 初始化默认人群分布。
- 生成基础 Agent Archetype。
- 给默认权重提供 evidence。

### 4.2 平台级画像

平台包括：

- 番茄。
- 起点。
- 晋江。
- 抖音短剧。
- 快手短剧。
- 微信小程序短剧。

用途：

- 调整平台权重。
- 调整行为阈值。
- 调整推荐流信号。

### 4.3 项目级画像

来源：

- 某部作品真实评论。
- 完读/完播。
- 追更。
- 付费。
- 好评。
- 作者或编辑反馈。

用途：

- 形成项目专属 Agent Memory。
- 修正当前作品读者偏好。

### 4.4 客户私有画像

来源：

- MCN / 短剧公司 / 工作室私有数据。

用途：

- 私有校准。
- 商业壁垒。
- 不同客户形成不同 Agent 记忆。

---

## 5. 数学分布设计

### 5.1 Categorical 分布

用于离散变量：

```text
age_group
city_tier
watch_frequency
platform_type
genre_cluster
```

示例：

```python
age_group ~ Categorical({
  "gen_z": 0.25,
  "age_26_45": 0.50,
  "age_45_60": 0.15,
  "age_60_plus": 0.10
})
```

```python
watch_frequency ~ Categorical({
  "daily": 0.3619,
  "weekly_multi": 0.3815,
  "occasional": 0.2566
})
```

### 5.2 Bernoulli 分布

用于是否类变量：

```python
repeat_watch ~ Bernoulli(p=0.6578)
```

### 5.3 Beta 分布

用于 0-1 连续偏好或行为倾向：

```python
paid_propensity ~ Beta(alpha=2.2, beta=4.0)
comment_propensity ~ Beta(alpha=1.5, beta=5.0)
share_propensity ~ Beta(alpha=1.2, beta=6.0)
face_slapping_preference ~ Beta(alpha=3.0, beta=2.0)
emotion_preference ~ Beta(alpha=2.8, beta=2.2)
quality_sensitivity ~ Beta(alpha=1.8, beta=3.0)
```

Beta 分布适合表示：

- 大多数人偏中低，少数人极高。
- 参数可被真实反馈逐步校准。

### 5.4 Dirichlet 分布

用于多偏好占比：

```python
genre_preference_vector ~ Dirichlet([
  revenge,
  romance,
  suspense,
  comedy,
  family,
  workplace
])
```

它适合表示一个用户对多个题材的相对偏好。

---

## 5.5 P1 默认分布参数

P1 需要一组可以直接落地的默认参数，建议写入：

```text
backend/config/audience_research.yaml
```

短剧默认：

```yaml
micro_drama_2024_default:
  source: "中国微短剧行业发展白皮书（2024）+ 公开行业资料整理"
  confidence: 0.62
  categorical_distributions:
    watch_frequency:
      daily: 0.3619
      weekly_multi: 0.3815
      occasional: 0.2566
    city_tier:
      tier_1_2: 0.30
      tier_3_lower: 0.70
  bernoulli_distributions:
    repeat_watch: 0.6578
  beta_distributions:
    paid_propensity: [2.2, 4.0]
    comment_propensity: [1.5, 5.0]
    share_propensity: [1.2, 6.0]
    face_slapping_preference: [3.0, 2.0]
    emotion_preference: [2.8, 2.2]
    quality_sensitivity: [1.8, 3.0]
  platform_feed_weights:
    retention: 0.30
    comment: 0.20
    paid_conversion: 0.20
    share: 0.15
    positive_review: 0.10
    platform_fit: 0.10
    dropoff_penalty: 0.25
```

网文默认：

```yaml
web_novel_2024_default:
  source: "2024中国网络文学蓝皮书 + 公开行业资料整理"
  confidence: 0.60
  categorical_distributions:
    age_group:
      gen_z: 0.25
      age_26_45: 0.50
      age_45_60: 0.15
      age_60_plus: 0.10
  beta_distributions:
    paid_propensity: [1.8, 4.5]
    comment_propensity: [1.3, 5.5]
    share_propensity: [1.1, 6.5]
    face_slapping_preference: [2.6, 2.4]
    emotion_preference: [2.5, 2.4]
    quality_sensitivity: [2.2, 2.8]
  platform_feed_weights:
    retention: 0.35
    positive_review: 0.20
    comment: 0.15
    paid_conversion: 0.15
    platform_fit: 0.15
```

这些参数是 P1 默认启发式参数，不是最终真实画像。后续必须通过真实反馈校准。

---

## 6. 少量 Agent 如何拟合总体

P1 不需要生成 1000 个 Agent。

目标是：

```text
用 4-7 个代表 Agent，近似真实用户总体的关键统计特征。
```

方法：

1. 根据宏观分布先采样一个虚拟 population，例如 500 或 1000 个样本。
2. 对样本按行为特征聚类。
3. 每个 cluster 生成一个代表 Agent。
4. 代表 Agent 的权重 = cluster 占比。
5. 校验代表 Agent 加权后的宏观统计是否接近目标分布。

这叫：

```text
population compression
```

不是简单手写权重。

### 6.1 可用方法

P1 推荐用：

```text
加权 KMeans / KMedoids / 分层分桶
```

如果不想引入复杂依赖，P1 先用分层分桶：

```text
platform_type
business_goal
watch_frequency
paid_propensity_bucket
content_preference_cluster
```

然后合并小桶，得到 4-7 个代表 Agent。

P1 必须控制代表 Agent 数量：

```text
最小：4 个
推荐：5-6 个
上限：7 个
```

如果拟合误差过高，优先调整：

- segment_weight。
- behavior_thresholds。
- platform_multiplier。
- genre_multiplier。
- business_goal_multiplier。
- Beta / Dirichlet 分布参数。

只有当某个真实人群在行为机制上无法被现有 Agent 表达时，才新增 Agent。

### 6.2 P1 推荐代表 Agent

短剧/网文通用 P1 推荐 6 个：

| Agent | 职责 | 主要通过哪些参数调节 |
|---|---|---|
| 爽点追更型 | 反杀、打脸、升级、主线推进 | face_slapping_preference, retention_threshold |
| 情感代入型 | 共情、虐恋、关系拉扯、好评 | emotion_preference, positive_review_threshold |
| 付费解锁型 | 章末钩子、未完成信息、付费 | paid_propensity, pay_threshold |
| 吐槽传播型 | 评论、玩梗、争议、二创 | comment_propensity, share_propensity |
| 品质口碑型 | 逻辑、人设、长期口碑 | quality_sensitivity, dropoff_threshold |
| 平台推流 Agent | 完读、评论、付费、分享、推荐 | feed_weights, platform_multiplier |

如果 P1 要进一步压缩到 4 个：

```text
爽点追更型
情感代入型
付费解锁型
平台推流 Agent
```

吐槽传播和品质口碑先作为参数并入上述 Agent：

```text
comment_propensity
quality_sensitivity
dropoff_threshold
```

### 6.3 4 个 Agent 如何承载更多人群

如果 P1 采用 4 个代表 Agent，不代表其他人群消失，而是通过参数维度进入这 4 个 Agent。

| 被压缩的人群 | 进入哪个 Agent | 通过什么参数表达 |
|---|---|---|
| 吐槽传播用户 | 爽点追更型 / 平台推流 Agent | comment_propensity, share_propensity, controversy_sensitivity |
| 品质口碑用户 | 情感代入型 / 平台推流 Agent | quality_sensitivity, logic_sensitivity, dropoff_threshold |
| 成熟长线读者 | 情感代入型 | quality_sensitivity, retention_tolerance, positive_review_threshold |
| 悬疑推理用户 | 爽点追更型 / 付费解锁型 | curiosity_preference, logic_sensitivity, hook_threshold |
| 下沉快感用户 | 爽点追更型 | face_slapping_preference, emotion_release, pay_threshold |

P1 调参优先级：

```text
先调参数
再调权重
再调分布
最后才新增 Agent
```

---

## 7. 统计拟合流程

```text
Load audience_research.yaml
-> Build AudienceDistributionConfig
-> Sample synthetic audience population
-> Compress population into representative agents
-> Validate weighted macro statistics
-> Save AgentProfileSet
-> Run simulation with representative agents
```

---

## 8. P1 Schema

### 8.1 AudienceDistributionConfig

```python
class AudienceDistributionConfig(BaseModel):
    distribution_id: str
    name: str
    source: str
    platform_type: str
    categorical_distributions: dict[str, dict[str, float]]
    bernoulli_distributions: dict[str, float]
    beta_distributions: dict[str, tuple[float, float]]
    dirichlet_distributions: dict[str, list[float]]
    confidence: float
```

### 8.2 SampledAudience

```python
class SampledAudience(BaseModel):
    sample_id: str
    age_group: str
    city_tier: str | None
    watch_frequency: str
    repeat_watch: bool
    platform_type: str
    genre_preferences: dict[str, float]
    behavior_propensities: dict[str, float]
    content_needs: dict[str, float]
```

### 8.3 RepresentativeAgentProfile

```python
class RepresentativeAgentProfile(BaseModel):
    agent_id: str
    name: str
    archetype: str
    cluster_size: int
    segment_weight: float
    centroid_features: dict[str, float]
    categorical_summary: dict[str, dict[str, float]]
    content_needs: dict[str, float]
    behavior_thresholds: dict[str, float]
    evidence: list[PersonaEvidence]
    confidence: float
```

### 8.4 PersonaEvidence

```python
class PersonaEvidence(BaseModel):
    source_type: Literal[
        "industry_report",
        "manual_expert",
        "real_feedback",
        "comment_sample",
        "simulation",
    ]
    source_name: str
    sample_size: int | None
    observed_metric: dict[str, float]
    confidence: float
```

### 8.5 PopulationFitReport

```python
class PopulationFitReport(BaseModel):
    target_distribution: dict
    representative_distribution: dict
    distribution_error: float
    max_feature_error: dict[str, float]
    accepted: bool
```

---

## 9. 误差控制

P1 必须验证代表 Agent 是否拟合宏观分布。

### 9.1 Categorical 误差

```python
categorical_error =
  sum(abs(sample_ratio[k] - target_ratio[k]) for k in categories)
```

### 9.2 连续变量误差

```python
mean_error = abs(sample_mean - target_mean)
```

### 9.3 接受阈值

P1 建议：

```text
distribution_error <= 0.08：接受
0.08 - 0.15：警告但可用
> 0.15：优先重新调参；只有调参仍无法覆盖时才增加代表 Agent
```

### 9.4 拟合误差如何影响最终报告

PopulationFitReport 不能只是开发者调试信息，它必须影响最终报告置信度。

```text
distribution_error <= 0.08:
  population_confidence = high

0.08 < distribution_error <= 0.15:
  population_confidence = medium

distribution_error > 0.15:
  population_confidence = low
```

最终报告置信度：

```text
final_confidence =
  base_simulation_confidence
  * population_fit_multiplier
  * evidence_confidence
```

建议 multiplier：

```text
high   -> 1.00
medium -> 0.85
low    -> 0.65
```

如果拟合误差为 low：

- 不允许输出 high confidence。
- 报告必须提示“当前代表 Agent 与目标宏观分布拟合不足”。
- 建议重新采样、调参或增加一个代表 Agent。

---

## 10. Evidence-based Agent Memory

Agent Memory 不能只是文字经验。

每条记忆必须包含：

```text
适用平台
适用题材
触发信号
预期指标影响
反向条件
证据来源
样本量
置信度
```

示例：

```json
{
  "pattern_id": "wechat_identity_hook_001",
  "description": "身份线索在付费前未完全揭露时，微信小程序短剧付费意愿通常上升；但若前一集已经明显泄露，效果下降。",
  "applies_to_platforms": ["wechat_minidrama"],
  "applies_to_genres": ["复仇", "甜虐", "豪门"],
  "signal": "身份线索未完全揭露",
  "expected_metric_effect": {
    "paid_conversion": 0.06,
    "retention": 0.03
  },
  "negative_conditions": [
    "前一集已明显泄露",
    "付费后没有兑现反击",
    "主角被动时间过长"
  ],
  "evidence": {
    "source_type": "real_feedback",
    "sample_size": 12,
    "confidence": 0.74
  }
}
```

低证据记忆只能参与解释，不直接改评分。

### 10.1 P1 人工校准

P1 还没有稳定真实平台数据时，可以允许人工专家或作者输入 evidence。

人工校准例子：

```json
{
  "source_type": "manual_expert",
  "source_name": "短剧编剧经验",
  "sample_size": null,
  "observed_metric": {
    "paid_conversion_effect": 0.04
  },
  "confidence": 0.55,
  "note": "微信小程序短剧中，女主长期被动会降低付费意愿；但如果下一集明确反杀，可转化为短期付费钩子。"
}
```

人工校准只能作为中低置信度 evidence。只有被真实反馈验证后，才能提升 confidence。

P1 支持的人工校准来源：

- 平台经验。
- 题材经验。
- 项目读者反馈。
- 评论关键词整理。
- 编辑意见。

---

## 11. P1 技术模块

```text
backend/
  config/
    audience_research.yaml
    agent_population.yaml
  population/
    distribution_loader.py
    sampler.py
    compressor.py
    validator.py
  schemas/
    audience_distribution.py
    population.py
    evidence.py
    calibration.py
  simulation/
    light_social_simulator.py
    feed_simulator.py
    comment_simulator.py
  memory/
    memory_store.py
    memory_selector.py
    memory_update_service.py
  api/
    population_routes.py
    memory_routes.py
    trace_routes.py
```

---

## 11.1 P0 到 P1 的代码改造点

P1 不应重写 P0，而是在 P0 上替换几个关键模块。

### `simulation/agent_profile.py`

当前：

```text
硬编码 P0_MARKET_AGENTS
```

P1：

```text
从 AgentProfileSet 加载 4-7 个代表 Agent
```

新增：

```text
population/distribution_loader.py
population/sampler.py
population/compressor.py
population/validator.py
```

### `services/demo_runner.py`

当前：

```text
run_round_one(world, drafts)
```

P1：

```text
profile_set = load_or_build_agent_profile_set(platform_type, genre, business_goal)
run_round_one(world, drafts, profile_set)
```

### `schemas/`

新增：

```text
audience_distribution.py
population.py
evidence.py
calibration.py
```

### `api/`

新增：

```text
GET /api/population/profile-set
GET /api/population/fit-report
GET /api/traces
GET /api/traces/{simulation_id}
GET /api/agents/{agent_id}/memory
POST /api/agents/{agent_id}/memory/patterns
```

### 前端

P0 Swagger / 简单页面：

```text
输入 -> 报告
```

P1 React/Vite：

```text
输入 -> 报告 -> Trace History -> Agent Population Inspector -> Memory Inspector
```

---

## 12. P1 前端方向

P1 前端建议从 static HTML 升级为：

```text
React + Vite
```

原因：

- P1 已经开始有项目输入、报告、历史记录、Agent 配置、Memory 查看。
- static HTML 会很快变乱。
- React/Vite 比 Next.js 轻，但比纯 HTML 更接近商业化产品骨架。

P1 页面：

```text
Project Input
Simulation Result
Trace History
Agent Population / Memory Inspector
```

---

## 13. P1 仍然不做什么

P1 不做：

- 完整 OASIS 接入。
- 百万 Agent。
- 真实推荐系统。
- 自动校准生产模型。
- 登录权限。
- 大规模向量库。

P1 只建立：

```text
真实宏观数据 -> 数学分布 -> 少量代表 Agent -> 拟合校验 -> 轻量模拟
```

---

## 14. P1 验收标准

1. 系统能加载 `audience_research.yaml`。
2. 系统能根据分布采样生成 synthetic audience。
3. 系统能压缩成 4-7 个代表 Agent。
4. 每个代表 Agent 有权重、画像、阈值和 evidence。
5. 系统能输出 PopulationFitReport。
6. 模拟时使用代表 Agent + 参数配置，而不是通过不断新增 Agent 覆盖差异。
7. Agent Memory 支持 evidence/source/confidence。
8. 前端能查看代表 Agent 和拟合误差。
9. simple-run 或正式 simulation 能使用统计拟合后的 AgentProfileSet。
10. 无真实反馈时可用行业数据初始化；有真实反馈后可生成 CalibrationRecord。

---

## 15. 结论

P1 的核心不是简单加几个 Agent，而是从：

```text
手工人设 Agent
```

升级为：

```text
统计拟合 Agent Population
```

最终产品的可信度来自：

```text
公开宏观数据约束总体分布
数学分布生成虚拟观众
少量代表 Agent 压缩总体
拟合误差报告证明代表性
真实反馈持续校准分布参数
```

这条路线能让我们用较少 Agent 获得更接近真实世界的模拟效果，同时为商业化阶段的私有数据校准打下架构基础。
