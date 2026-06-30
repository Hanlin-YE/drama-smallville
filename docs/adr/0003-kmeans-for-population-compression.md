# KMeans 压缩人口的选择理由

## 上下文

`compressor.py` 把 500 个采样观众压缩成 4-6 个代表性 Persona。聚类算法有三个候选：
- **KMeans**：假设球形簇，欧氏距离，O(nkd)，sklearn 成熟实现。
- **GMM（高斯混合）**：允许椭圆簇，软分配（每个点有属于各簇的概率），需指定协方差类型。
- **层次聚类（Agglomerative）**：不需要预设 k，可输出树状图，但 O(n²) 内存。

## 决定

采用 **KMeans**，`n_clusters=max_agents, random_state=42, n_init=10`。

## 理由

1. **够用**：观众行为特征（付费倾向×情感偏好×genre 偏好）虽然不完美球形，但 KMeans 的目标是把高维空间切成相对均匀的块——对"找 4-6 个代表"这个任务足够。
2. **快**：500 个样本 × 20 维特征，KMeans < 100ms。GMM 慢 3-5x，层次聚类 O(n²) 在 500 样本时已明显。
3. **可解释**：KMeans 的 centroid 就是"这个 Persona 的平均特征"，直接映射到 `RepresentativeAgentProfile.centroid_features`。GMM 的软分配在解释上多一层。
4. **兜底已有**：`_compress_with_kmeans` 失败时（sklearn 未安装）降级到 `_assign_archetype`（基于规则的桶分配），保证无 sklearn 环境也能跑。

## 被否决的方案

- **GMM**：允许椭圆簇理论上更贴合，但 P0 阶段观众特征分布的协方差结构未知，GMM 的额外参数（covariance type）增加调参负担。
- **层次聚类**：O(n²) 在 500 样本可接受，但未来扩展到 5000 样本时会爆。且不需要树状图——我们只要 4-6 个 flat cluster。

## 后果

- KMeans 假设球形簇可能导致非球形人群（如"高付费但低评论"的长尾群体）被拆散。`_ensure_anchor_coverage` 补救了两个关键 archetype（paid_unlock / platform_feed），其余的靠 P1 真实数据校准。
- `random_state=42` 固定种子保证可复现。换种子结果会变，需在 P1 评估稳定性。
