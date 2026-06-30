# 项目拷问报告 — 爆款短剧推演 / Drama Smallville

> 拷问日期：2026-06-30｜方法：grill-project 六大维度｜场景：评估既有项目成熟度

## 一句话结论

**领域语言和架构决策（左组）明显成熟于代码结构与可运行性（右组）。文档很体面，但项目差点跑不起来——环境是 Windows 造的，macOS 上完全不可用。** 今天已修复可运行性基线；下一步的杠杆在前后端打通与可测试性下沉。

---

## 一、六大维度评分

| 维度 | 评分 | 状态 |
|---|---|---|
| 1. 统一领域语言 | 4.5 / 5 | 成熟 |
| 2. 边界压测（场景） | 4.0 / 5 | 成熟偏缺口 |
| 3. ADR 克制 | 4.5 / 5 | 成熟 |
| 4. 深模块 | 3.5 / 5 | 有缺口 |
| 5. Seam 放置 | 3.0 / 5 | 缺口明显 |
| 6. 可测试性 | 3.5 / 5 | 有缺口（基线已修） |

**总分 23 / 30。** 左组（思考沟通）12.5/15，右组（代码结构）10/15。典型的"想得清楚、落地欠一截"。

---

## 二、各维度现状与缺口

### 1. 统一领域语言 — 成熟（4.5）

**证据**：`CONTEXT.md` 定义 9 个术语，每个带 `_Avoid_` 反表，禁用裸 "Agent"；待定术语（confidence 算法、剧本医生记忆 schema）单独列出不混入正文。这是本项目最强的一面。

**缺口**：
- `AgentProfile` → `PersonaProfile` 改名未落地（PRD §7.1 待办，`simulation/agent_profile.py` 仍叫 AgentProfile，与 LLM Agent 重载）。
- `confidence = 0.72` 在 `agents/audience_agents.py:97` 硬编码，CONTEXT 已标"待定"但没写 ADR 记录来源。

**下一个该回答的问题**：`AgentProfile` 改名牵涉多少调用点？是现在改（趁 backend 还小），还是等 P1？（推荐：现在改，成本只升不降。）

### 2. 边界压测（场景） — 成熟偏缺口（4.0）

**证据**：ADR-0003 用"5000 样本时层次聚类会爆"压测聚类选型；ADR-0004 用"爽点追更型判断靠内容不靠环境"压测 Round 2 key_agents 边界。没用"灵活性/扩展性"这种空话。

**缺口**：
- ADR-0004 已承认 `key_agents` 集合新旧命名混用（`audience_paid_unlock` + `paid_unlock`），是已知技术债。
- PRD §9"范围膨胀"风险仍是抽象词，没场景化（"如果有人要加 RAG，拒绝的判据是什么？"）。

**下一个该回答的问题**：Round 2 的 6 个 key_agents 是硬编码集合——如果未来 P1 用 KMeans 压缩出不同 archetype 名，这套硬编码会失配。现在该用 archetype 特征匹配还是 ID 匹配？

### 3. ADR 克制 — 成熟（4.5）

**证据**：只有 4 个 ADR，每个都满足"难逆转 + 没上下文会困惑 + 真权衡"三条。ADR-0001（ScriptMind 工具层）、0002（降级）、0003（KMeans）、0004（Round2 key_agents）质量高，无噪音。这点绝大多数项目做不到。

**缺口**：`confidence = 0.72` 硬编码符合 ADR 候选（难逆转、会困惑、有真权衡——0.72 vs 真实数据），但没写。

**下一个该回答的问题**：0.72 该不该现在补一个 ADR-0005？（推荐：该，一行字记录"来源是启发式占位，P1 用真实数据替换"。）

### 4. 深模块 — 有缺口（3.5）

**证据**：`compress_population` 接口小（3 参数）实现大（324 行，KMeans + 兜底 + anchor 覆盖），是深模块典型。`_judge_draft` 已从 183 行上帝函数拆成 `_build_judge_text` / `_score_keywords` / `_apply_goal_boost` / `_generate_risks_triggers` 四个，杠杆变高。

**缺口**：
- `audience_agents.py` 拆分后留了 `if False else 0.0` 死代码（**今天已清**）。
- `real_audience` 通过 `parents[3]/"real_audience"/profiles/...` 硬编码相对路径耦合进 `population/distribution_loader.py`——模块边界靠目录层级数硬连，换目录就断。

**下一个该回答的问题**：`real_audience` 该作为 backend 的注入依赖（port + adapter），还是保持文件路径耦合？（推荐：注入，因为 `parents[3]` 是隐式契约，迁移即崩。）

### 5. Seam 放置 — 缺口明显（3.0）

**证据**：ScriptMind 作为外部依赖，seam 设计得好——`llm/gateway.py` 是 port，`script_mind_client.py` 是 adapter，`demo_runner` 注入 gateway，ADR-0002 降级路径实测通过。这是对的。

**缺口**：
- **frontend / backend / ui-demo 三者割裂**：`ui-demo/writers-room-demo.html` 是纯静态 mockup（零 fetch，不与后端通信）；`frontend/` 是 Vite+React 但 `src/` 只有 `main.tsx` + `styles.css` 空壳，且无 `tsconfig.json`；backend 的 `static/index.html` 又是另一套。三个"前端"互不相干，没有 seam。
- 前后端没有约定接口契约（OpenAPI 在 backend，但 frontend 不消费它）。

**下一个该回答的问题**：这三个"前端"到底留哪个？（推荐：砍 ui-demo 和 frontend 空壳，留 backend/static/index.html 做最小可路演 UI，或明确 frontend 是 P1 目标并补 tsconfig + 接口消费。现在三套并存是噪音。）

### 6. 可测试性 — 有缺口（3.5，基线已修）

**证据**：19 个测试覆盖 sampler/compressor/validator/_judge_draft 拆分，`tests/factories.py` 有工厂函数，pytest 痕迹真实。`_judge_draft` 拆分后测试穿过 seam，符合"接口即测试面"。

**缺口**：
- **可运行性基线今天刚修**：原 `.venv` 是 Windows 造的（`home = D:\AppDownload\Python`），macOS 完全不可用；`requirements.txt` 缺 numpy/scikit-learn（ADR-0003 选的 KMeans 走不了真路径，只能降级）。**已重建 macOS venv + 补全依赖，19 测试 17.7s 全过。**
- 测试只覆盖底层管线，**API 层 0 测试**（8 个端点无端到端测试，靠手动 curl）。
- 测试靠 `sys.path.insert` hack，无 `pytest.ini`/`pyproject.toml`。
- Trace 回放/对比缺失（PRD §7.4 待办，只有 save 无 load/compare）。

**下一个该回答的问题**：API 层该不该现在补端到端测试？（推荐：该，且成本低——用 TestClient + `tests/factories.py` 已有工厂，3-5 个测试覆盖 demo-run/simple-run/trace 的 happy path。）

---

## 三、最该先解决的三个缺口（按杠杆排序）

1. **前后端打通 / 砍掉冗余前端**（杠杆最高，Seam 维度）。三个"前端"并存是结构性噪音，决定了项目能不能给人看。先决策留哪个。
2. **API 层端到端测试**（可测试性维度）。底层有测试、API 层裸奔，是测试覆盖的断层。成本低、信心收益大。
3. **`real_audience` 解耦 + `AgentProfile` 改名**（深模块 + 语言维度）。两个已知技术债，趁 backend 还小（45 个 .py / ~3670 行）现在改最便宜。

---

## 四、今天（2026-06-30）已完成的修改

| # | 修改 | 文件 | 说明 |
|---|---|---|---|
| 1 | 重建 macOS venv | `.venv/`（旧 → `.venv.windows-backup/`） | 旧 venv 是 Windows 造的，macOS 不可用；用 managed python 3.13.12 重建 |
| 2 | 补全依赖清单 | `script simulation/backend/requirements.txt` | 加 `numpy` / `scikit-learn` / `pytest`，让 ADR-0003 的 KMeans 走真路径 |
| 3 | 验证基线 | — | 19 个测试 17.7s 全过；后端 import 链全通；`/health` 200；8 个业务端点均在 openapi 注册；`/api/traces` 返回真实数据 |
| 4 | plandb 加执行位 | `tools/plandb` | 原 `-rw-rw-rw-` 无 x，`chmod +x`；AGENTS.md 的 `./tools/plandb status` 现可跑 |
| 5 | PRD 路径约定 | `PRD.md` | 加"路径约定与模块布局"段，统一所有 backend 路径相对于 `script simulation/backend/`，并列出真实模块分布 |
| 6 | PRD feedback 层标注 | `PRD.md` §3.1 | `storage/feedback/` 实际不存在，标注"尚未实现" |
| 7 | PRD schemas 路径 | `PRD.md` §5 | `backend/schemas/` → `schemas/`（与路径约定一致） |
| 8 | backend README 补依赖说明 | `script simulation/backend/README.md` | 加 Prerequisites 段：Python 版本、依赖清单、venv 建立、降级说明、测试命令 |
| 9 | 扩充 .gitignore | `.gitignore` | 加 `__pycache__/` / `*.pyc` / `.pytest_cache/` / `node_modules/` / `dist/` / `.venv.windows-backup/` |
| 10 | 清理死代码 | `agents/audience_agents.py` | 删 `_score_keywords` 里 `if False else 0.0` 的拆分遗留死代码 |

**验证方式**：`cd "script simulation/backend" && ../../.venv/bin/python -m pytest tests/ -v` → 19 passed。

---

## 五、下一步建议（按优先级）

### 一天内可继续做
- **API 层端到端测试**：用 TestClient + factories，3-5 个测试覆盖 `/api/drama/simple-run`、`/api/traces`、`/api/agents/{id}/memory` 的 happy path。
- **砍冗余前端**：决策 ui-demo / frontend 空壳 / backend static 三选一，移除其余两个或明确各自定位。
- **补 ADR-0005**：记录 `confidence = 0.72` 的来源与替换计划（一行字）。
- **加 `pyproject.toml` 或 `pytest.ini`**：替代 `sys.path.insert` hack，固定 pytest rootdir。

### 需要更长时间（不在今天范围）
- `AgentProfile` → `PersonaProfile` 全局改名（牵涉 schemas/agents/tests 多处）。
- `real_audience` 改为注入式 port（`distribution_loader` 不再硬编码 `parents[3]`）。
- Trace 回放/对比功能（PRD §7.4）。
- 剧本医生工作记忆 schema（PRD §3.4 待办）。
- 真实反馈导入 → CalibrationRecord 管线（PRD §3.4 待办）。

---

## 六、拷问过程中的两次"工具视角"教训

1. **Glob `**/*.py` 被 .venv 的 pip 文件挤过 100 条上限截断**，导致 `api/population_routes.py` 没出现在结果里，一度误判"main.py 引用不存在的模块"。复核 `api/**` 后推翻。
2. **`starlette-1.3.1` 用 `_IncludedRouter` 包装 include_router 的路由**，直接遍历 `app.routes` 看不到子路由的 path，一度误判"API 层是空壳、8 个端点全没注册"。用 TestClient 实际请求 + openapi.json 双重验证后推翻。

**结论**：grill 的"用具体场景压测、别停留在概念遍历"不只是对领域设计，对代码核查同样成立。每个"它不存在/它坏了"的判断，都要用一个能跑的动作去证伪一次。
