import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type CandidateDraft = {
  draft_id: string;
  title: string;
  synopsis: string;
  script_text?: string | null;
  key_beats: string[];
  intended_hook: string;
  intended_emotion: string;
  expected_reader_action: "continue_reading" | "give_positive_review" | "pay_to_unlock" | "comment" | "share";
  locked_by_author?: boolean;
  author_note?: string | null;
};

type QualityScore = {
  draft_id: string;
  final_score: number;
  retention_score: number;
  positive_review_score: number;
  paid_conversion_score: number;
  platform_recommendation_score: number;
  logic_consistency_score?: number;
  character_consistency_score?: number;
  hook_strength_score?: number;
  emotional_intensity_score?: number;
  disagreement_penalty?: number;
};

type CreativeReview = {
  agent_id: string;
  draft_id: string;
  score: number;
  opinion: string;
  suggested_revision: string;
  must_fix: boolean;
  author_intent_conflict: boolean;
};

type AudienceJudgment = {
  agent_id: string;
  draft_id: string;
  round_id: "round_1" | "round_2" | string;
  continue_watch: number;
  positive_review: number;
  pay: number;
  comment: number;
  share: number;
  dropoff: number;
  platform_recommendation?: number | null;
  trigger_points: string[];
  risk_points: string[];
  revised_from_previous_round?: boolean;
  revision_reason?: string | null;
  confidence: number;
};

type Report = {
  simulation_id: string;
  recommended_draft_id: string | null;
  initial_winner_draft_id: string | null;
  winner_changed: boolean;
  confidence_level: "high" | "medium" | "low";
  confidence_score: number;
  no_strong_recommendation: boolean;
  candidate_drafts: CandidateDraft[];
  quality_scores: QualityScore[];
  creative_reviews: CreativeReview[];
  audience_judgments: AudienceJudgment[];
  key_disagreements: string[];
  biggest_dropoff_risk: string;
  strongest_paid_trigger: string;
  platform_recommendation_summary: string;
  confidence_reasons: string[];
  rewrite_recommendations: string[];
  next_iteration_prompt: string;
  markdown?: string | null;
};

type PopulationFitReport = {
  target_distribution: Record<string, unknown>;
  representative_distribution: Record<string, unknown>;
  distribution_error: number;
  max_feature_error: Record<string, number>;
  accepted: boolean;
  confidence_level: string;
};

type RepresentativeAgentProfile = {
  agent_id: string;
  name: string;
  archetype: string;
  cluster_size: number;
  segment_weight: number;
  centroid_features: Record<string, number>;
  categorical_summary: Record<string, Record<string, number>>;
  content_needs: Record<string, number>;
  behavior_thresholds: Record<string, number>;
  confidence: number;
  evidence?: Array<Record<string, unknown>>;
};

type AgentProfileSet = {
  profile_set_id: string;
  platform_type: string;
  business_goal: string;
  representative_agents: RepresentativeAgentProfile[];
  distribution_id: string;
  population_fit: PopulationFitReport;
};

type MemoryPattern = {
  description?: string;
  applies_to_platforms?: string[];
  applies_to_genres?: string[];
  signal?: string | null;
  expected_metric_effect?: Record<string, number>;
  negative_conditions?: string[];
  evidence?: {
    confidence?: number;
    source?: string;
    source_type?: string;
    [key: string]: unknown;
  };
};

type AgentMemory = {
  agent_id?: string;
  memory_version?: string;
  confidence?: number;
  learned_patterns?: MemoryPattern[];
  [key: string]: unknown;
};

type AgentMessage = {
  message_id: string;
  round_id: string;
  from_agent: string;
  to_agent: string;
  message_type: string;
  content: string;
  referenced_draft_id?: string | null;
};

type TraceRecord = {
  simulation_id: string;
  schema_version: string;
  created_at: string;
  input?: { title?: string; platform_type?: string; business_goal?: string };
  candidate_drafts?: CandidateDraft[];
  creative_reviews?: CreativeReview[];
  audience_judgments?: AudienceJudgment[];
  agent_messages?: AgentMessage[];
  model_settings?: {
    model?: string;
    mode?: string;
    profile_set_id?: string;
    population_fit?: PopulationFitReport;
    [key: string]: unknown;
  };
  prompt_versions?: Record<string, string>;
};

type SupportState = {
  loading: boolean;
  population: AgentProfileSet | null;
  trace: TraceRecord | null;
  memory: AgentMemory | null;
  errors: string[];
};

type TabKey = "overview" | "drafts" | "audience" | "evidence";
type AudienceMetric = "continue_watch" | "positive_review" | "pay" | "comment" | "share" | "dropoff";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const platformLabels: Record<string, string> = {
  wechat_minidrama: "微信小程序短剧",
  douyin_short_drama: "抖音短剧",
  kuaishou_short_drama: "快手短剧",
  fanqie: "番茄",
  qidian: "起点",
  jinjiang: "晋江",
  other: "其他"
};

const goalLabels: Record<string, string> = {
  retention: "留存",
  positive_review: "好评",
  paid_conversion: "付费",
  platform_recommendation: "平台推荐"
};

const actionLabels: Record<CandidateDraft["expected_reader_action"], string> = {
  continue_reading: "继续看",
  give_positive_review: "给好评",
  pay_to_unlock: "付费解锁",
  comment: "评论",
  share: "分享"
};

const audienceMetrics: Array<{ key: AudienceMetric; label: string; tone: "good" | "warn" | "risk" }> = [
  { key: "continue_watch", label: "留存", tone: "good" },
  { key: "positive_review", label: "好评", tone: "good" },
  { key: "pay", label: "付费", tone: "good" },
  { key: "comment", label: "评论", tone: "warn" },
  { key: "share", label: "分享", tone: "warn" },
  { key: "dropoff", label: "弃坑", tone: "risk" }
];

const initialSupport: SupportState = {
  loading: false,
  population: null,
  trace: null,
  memory: null,
  errors: []
};

function App() {
  const [title, setTitle] = useState("Neon Case：镜城零点案");
  const [text, setText] = useState("");
  const [platformType, setPlatformType] = useState("other");
  const [businessGoal, setBusinessGoal] = useState("retention");
  const [genre, setGenre] = useState("剧情测试");
  const [authorStyle, setAuthorStyle] = useState("作者驱动、虚拟试播");
  const [authorIntent, setAuthorIntent] = useState("");
  const [mustKeep, setMustKeep] = useState("核心冲突、人物动机、下一步钩子");
  const [avoid, setAvoid] = useState("强行完结、无解释反转");
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [support, setSupport] = useState<SupportState>(initialSupport);

  async function run(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setReport(null);
    setSupport(initialSupport);

    try {
      const response = await fetch(`${API_BASE}/api/drama/simple-run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          text,
          platform_type: platformType,
          business_goal: businessGoal,
          genre: splitList(genre),
          author_style: splitList(authorStyle),
          author_intent: authorIntent,
          constraints: ["不要替作者做最终决定", "输出可执行改稿建议"],
          must_keep_elements: splitList(mustKeep),
          avoid_elements: splitList(avoid)
        })
      });
      if (!response.ok) {
        throw new Error(`主试播接口返回 HTTP ${response.status}`);
      }
      const data = (await response.json()) as Report;
      setReport(data);
      setActiveTab("overview");
      void loadSupportData(data.simulation_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败");
    } finally {
      setLoading(false);
    }
  }

  async function loadSupportData(simulationId: string) {
    setSupport({ ...initialSupport, loading: true });
    const populationUrl = `${API_BASE}/api/population/profile-set?platform_type=${encodeURIComponent(platformType)}&business_goal=${encodeURIComponent(businessGoal)}&max_agents=6&seed=42`;
    const traceUrl = `${API_BASE}/api/traces/${encodeURIComponent(simulationId)}`;
    const memoryUrl = `${API_BASE}/api/agents/screenwriter/memory`;

    const [populationResult, traceResult, memoryResult] = await Promise.allSettled([
      fetchJson<AgentProfileSet>(populationUrl),
      fetchJson<TraceRecord>(traceUrl),
      fetchJson<AgentMemory>(memoryUrl)
    ]);

    const errors: string[] = [];
    if (populationResult.status === "rejected") errors.push(`人口拟合读取失败：${readError(populationResult.reason)}`);
    if (traceResult.status === "rejected") errors.push(`Trace 读取失败：${readError(traceResult.reason)}`);
    if (memoryResult.status === "rejected") errors.push(`编剧记忆读取失败：${readError(memoryResult.reason)}`);

    setSupport({
      loading: false,
      population: populationResult.status === "fulfilled" ? populationResult.value : null,
      trace: traceResult.status === "fulfilled" ? traceResult.value : null,
      memory: memoryResult.status === "fulfilled" ? memoryResult.value : null,
      errors
    });
  }

  return (
    <main className="workspace">
      <aside className="inputPane">
        <div>
          <p className="eyebrow">Drama Smallville</p>
          <h1>作者试播工作台</h1>
          <p className="sub">把剧情草稿交给虚拟观众和剧本医生，拿到下一轮可执行改稿方向。</p>
        </div>

        <form className="controlStack" onSubmit={run}>
          <label>
            剧名
            <input value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>

          <div className="row">
            <label>
              平台
              <select value={platformType} onChange={(event) => setPlatformType(event.target.value)}>
                <option value="wechat_minidrama">微信小程序短剧</option>
                <option value="douyin_short_drama">抖音短剧</option>
                <option value="kuaishou_short_drama">快手短剧</option>
                <option value="fanqie">番茄</option>
                <option value="qidian">起点</option>
                <option value="jinjiang">晋江</option>
                <option value="other">其他</option>
              </select>
            </label>
            <label>
              目标
              <select value={businessGoal} onChange={(event) => setBusinessGoal(event.target.value)}>
                <option value="retention">留存</option>
                <option value="positive_review">好评</option>
                <option value="paid_conversion">付费</option>
                <option value="platform_recommendation">平台推荐</option>
              </select>
            </label>
          </div>

          <div className="row">
            <label>
              题材
              <input value={genre} onChange={(event) => setGenre(event.target.value)} placeholder="短剧、悬疑、甜宠" />
            </label>
            <label>
              作者风格
              <input value={authorStyle} onChange={(event) => setAuthorStyle(event.target.value)} placeholder="爽文、强反转、慢热" />
            </label>
          </div>

          <label className="textLabel">
            剧情文本
            <textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="把当前剧情、人物设定或剧本片段粘贴到这里..."
            />
          </label>

          <label>
            作者意图
            <input
              value={authorIntent}
              onChange={(event) => setAuthorIntent(event.target.value)}
              placeholder="例如：女主不要立刻原谅男主，保持清醒和主动"
            />
          </label>

          <div className="row">
            <label>
              必须保留
              <input value={mustKeep} onChange={(event) => setMustKeep(event.target.value)} />
            </label>
            <label>
              避免元素
              <input value={avoid} onChange={(event) => setAvoid(event.target.value)} />
            </label>
          </div>

          <button className="primaryButton" type="submit" disabled={loading || !text.trim()}>
            {loading ? "试播中..." : "开始虚拟试播"}
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      </aside>

      <section className="resultPane">
        {!report && !loading && <EmptyState />}
        {loading && <LoadingState />}
        {report && (
          <>
            <ReportHeader report={report} platformType={platformType} businessGoal={businessGoal} />
            <nav className="tabBar" aria-label="结果视图">
              <TabButton tab="overview" activeTab={activeTab} onClick={setActiveTab}>总览</TabButton>
              <TabButton tab="drafts" activeTab={activeTab} onClick={setActiveTab}>候选稿</TabButton>
              <TabButton tab="audience" activeTab={activeTab} onClick={setActiveTab}>观众矩阵</TabButton>
              <TabButton tab="evidence" activeTab={activeTab} onClick={setActiveTab}>证据链</TabButton>
            </nav>
            {activeTab === "overview" && <Overview report={report} />}
            {activeTab === "drafts" && <Drafts report={report} />}
            {activeTab === "audience" && <AudienceMatrix report={report} />}
            {activeTab === "evidence" && <EvidencePanel report={report} support={support} />}
          </>
        )}
      </section>
    </main>
  );
}

function EmptyState() {
  return (
    <div className="emptyState">
      <p className="eyebrow">Pipeline Ready</p>
      <h2>后端优化会在这里转成创作判断。</h2>
      <div className="pipeline">
        {["候选稿生成", "剧本医生", "Persona 试播", "Round 2 复判", "Trace 证据"].map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="emptyState">
      <p className="eyebrow">Running Pilot</p>
      <h2>正在生成候选稿、审稿、模拟观众并聚合判断。</h2>
      <div className="loadingBar" />
    </div>
  );
}

function ReportHeader({ report, platformType, businessGoal }: { report: Report; platformType: string; businessGoal: string }) {
  const recommendation = report.no_strong_recommendation ? "暂无强推荐方案" : report.recommended_draft_id || "暂无推荐";
  return (
    <header className={`reportHero ${report.no_strong_recommendation ? "isLowConfidence" : ""}`}>
      <div>
        <p className="eyebrow">试播结果</p>
        <h2>{recommendation}</h2>
        <p className="subtle">
          {platformLabels[platformType] || platformType} · {goalLabels[businessGoal] || businessGoal} · {report.simulation_id}
        </p>
      </div>
      <div className="heroStats" aria-label="试播摘要">
        <MetricPill label="置信度" value={`${report.confidence_level} / ${report.confidence_score.toFixed(2)}`} />
        <MetricPill label="初始赢家" value={report.initial_winner_draft_id || "无"} />
        <MetricPill label="换榜" value={report.winner_changed ? "是" : "否"} />
      </div>
    </header>
  );
}

function Overview({ report }: { report: Report }) {
  return (
    <div className="contentStack">
      <section className="insightGrid" aria-label="关键洞察">
        <InsightCard label="最大弃坑风险" value={report.biggest_dropoff_risk} tone="risk" />
        <InsightCard label="最强付费触发" value={report.strongest_paid_trigger} tone="good" />
        <InsightCard label="平台推荐摘要" value={report.platform_recommendation_summary} tone="warn" />
      </section>

      <section className="sectionBlock">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Confidence</p>
            <h3>为什么是这个结论</h3>
          </div>
          {report.no_strong_recommendation && <span className="badge risk">需要补强材料</span>}
        </div>
        <ul className="plainList">
          {report.confidence_reasons.map((reason) => <li key={reason}>{reason}</li>)}
        </ul>
        <div className="nextPrompt">
          <strong>下一轮提示</strong>
          <p>{report.next_iteration_prompt}</p>
        </div>
      </section>

      <section className="scoreGrid">
        {report.quality_scores.map((score) => (
          <QualityScoreCard key={score.draft_id} score={score} />
        ))}
      </section>

      <section className="sectionBlock">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Rewrite</p>
            <h3>改稿建议</h3>
          </div>
        </div>
        <ul className="plainList">
          {report.rewrite_recommendations.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>
    </div>
  );
}

function Drafts({ report }: { report: Report }) {
  const reviewsByDraft = useMemo(() => groupBy(report.creative_reviews, (item) => item.draft_id), [report.creative_reviews]);
  const scoresByDraft = useMemo(() => indexBy(report.quality_scores, (item) => item.draft_id), [report.quality_scores]);

  return (
    <div className="contentStack">
      {report.candidate_drafts.map((draft) => {
        const score = scoresByDraft[draft.draft_id];
        const reviews = reviewsByDraft[draft.draft_id] || [];
        return (
          <article className="draftCard" key={draft.draft_id}>
            <div className="draftTopline">
              <div>
                <p className="eyebrow">{draft.draft_id}</p>
                <h3>{draft.title}</h3>
              </div>
              <span className="badge">{actionLabels[draft.expected_reader_action]}</span>
            </div>
            <p className="draftSynopsis">{draft.synopsis}</p>
            {draft.script_text && <pre className="storyText">{draft.script_text}</pre>}
            <div className="beatList">
              {draft.key_beats.map((beat) => <span key={beat}>{beat}</span>)}
            </div>
            <div className="draftMeta">
              <p><strong>钩子</strong>{draft.intended_hook}</p>
              <p><strong>情绪</strong>{draft.intended_emotion}</p>
              {draft.author_note && <p><strong>备注</strong>{draft.author_note}</p>}
            </div>
            {score && (
              <div className="compactMetrics">
                <ScoreBar label="综合" value={score.final_score} tone="good" />
                <ScoreBar label="钩子" value={score.hook_strength_score ?? 0} tone="warn" />
                <ScoreBar label="人物" value={score.character_consistency_score ?? 0} tone="good" />
                <ScoreBar label="分歧扣分" value={score.disagreement_penalty ?? 0} tone="risk" />
              </div>
            )}
            <div className="reviewList">
              {reviews.map((review) => (
                <div className="reviewRow" key={`${review.agent_id}-${review.draft_id}`}>
                  <div>
                    <strong>{agentLabel(review.agent_id)}</strong>
                    <span>{review.score}/100</span>
                  </div>
                  <p>{review.opinion}</p>
                  <small>{review.suggested_revision}</small>
                  <div className="badgeLine">
                    {review.must_fix && <span className="badge risk">必须修</span>}
                    {review.author_intent_conflict && <span className="badge warn">冲突作者意图</span>}
                  </div>
                </div>
              ))}
            </div>
          </article>
        );
      })}
    </div>
  );
}

function AudienceMatrix({ report }: { report: Report }) {
  const judgmentsByDraft = useMemo(() => groupBy(report.audience_judgments, (item) => item.draft_id), [report.audience_judgments]);

  return (
    <div className="contentStack">
      {report.candidate_drafts.map((draft) => {
        const judgments = judgmentsByDraft[draft.draft_id] || [];
        const roundOne = judgments.filter((item) => item.round_id === "round_1");
        const roundTwo = judgments.filter((item) => item.round_id === "round_2");
        return (
          <section className="audienceBlock" key={draft.draft_id}>
            <div className="sectionHeader">
              <div>
                <p className="eyebrow">{draft.draft_id}</p>
                <h3>{draft.title}</h3>
              </div>
              <span className="badge">{roundOne.length} + {roundTwo.length} 判断</span>
            </div>
            <div className="matrixTable" role="table" aria-label={`${draft.draft_id} 观众矩阵`}>
              <div className="matrixHead" role="row">
                <span>轮次</span>
                {audienceMetrics.map((metric) => <span key={metric.key}>{metric.label}</span>)}
              </div>
              <AudienceRoundRow label="Round 1" judgments={roundOne} />
              <AudienceRoundRow label="Round 2" judgments={roundTwo} />
            </div>
            <div className="signalGrid">
              <SignalList title="触发点" items={collectSignals(judgments, "trigger_points")} />
              <SignalList title="风险点" items={collectSignals(judgments, "risk_points")} />
              <SignalList title="二轮修正" items={roundTwo.map((item) => item.revision_reason || "读取环境摘要后保持原判断。")} />
            </div>
          </section>
        );
      })}
    </div>
  );
}

function AudienceRoundRow({ label, judgments }: { label: string; judgments: AudienceJudgment[] }) {
  return (
    <div className="matrixRow" role="row">
      <strong>{label}</strong>
      {audienceMetrics.map((metric) => (
        <span className={metric.tone} key={metric.key}>{formatPercent(avgMetric(judgments, metric.key))}</span>
      ))}
    </div>
  );
}

function EvidencePanel({ report, support }: { report: Report; support: SupportState }) {
  const messages = support.trace?.agent_messages || [];
  const patterns = support.memory?.learned_patterns || [];
  return (
    <div className="contentStack">
      {support.loading && <p className="supportNote">正在读取人口拟合、Trace 与编剧记忆...</p>}
      {support.errors.length > 0 && (
        <div className="supportWarning">
          {support.errors.map((item) => <p key={item}>{item}</p>)}
        </div>
      )}

      <section className="sectionBlock">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Population Fit</p>
            <h3>这批观众怎么来的</h3>
          </div>
          {support.population && (
            <span className={`badge ${support.population.population_fit.accepted ? "good" : "risk"}`}>
              {support.population.population_fit.accepted ? "拟合通过" : "拟合偏弱"}
            </span>
          )}
        </div>
        {support.population ? (
          <>
            <div className="fitStrip">
              <MetricPill label="Profile Set" value={support.population.profile_set_id} />
              <MetricPill label="误差" value={support.population.population_fit.distribution_error.toFixed(3)} />
              <MetricPill label="置信" value={support.population.population_fit.confidence_level} />
            </div>
            <div className="personaGrid">
              {support.population.representative_agents.map((persona) => (
                <article className="personaCard" key={persona.agent_id}>
                  <div>
                    <strong>{persona.name}</strong>
                    <span>{persona.archetype}</span>
                  </div>
                  <p>覆盖 {formatPercent(persona.segment_weight)} · 样本 {persona.cluster_size} · 置信 {persona.confidence.toFixed(2)}</p>
                  <small>{topEntries(persona.content_needs).join(" / ") || "内容需求未标注"}</small>
                </article>
              ))}
            </div>
          </>
        ) : (
          <p className="muted">人口拟合暂不可用，主试播报告仍可继续使用。</p>
        )}
      </section>

      <section className="sectionBlock">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Working Memory</p>
            <h3>编剧记忆只读展示</h3>
          </div>
          <span className="badge">不写入</span>
        </div>
        {patterns.length ? (
          <div className="memoryList">
            {patterns.slice(0, 5).map((pattern, index) => (
              <article className="memoryItem" key={`${pattern.description}-${index}`}>
                <strong>{pattern.description || "未命名经验"}</strong>
                <p>{(pattern.applies_to_platforms || []).join("、") || "全平台"} · 置信 {(pattern.evidence?.confidence ?? 0).toFixed(2)}</p>
                {pattern.signal && <small>{pattern.signal}</small>}
              </article>
            ))}
          </div>
        ) : (
          <p className="muted">暂无可展示的编剧记忆，或记忆接口不可用。</p>
        )}
      </section>

      <section className="sectionBlock">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Trace</p>
            <h3>系统如何判断</h3>
          </div>
          <span className="badge">{report.simulation_id}</span>
        </div>
        {support.trace ? (
          <>
            <div className="fitStrip">
              <MetricPill label="Schema" value={support.trace.schema_version} />
              <MetricPill label="模型模式" value={String(support.trace.model_settings?.mode || "-")} />
              <MetricPill label="消息数" value={String(messages.length)} />
            </div>
            <div className="timeline">
              {messages.slice(0, 10).map((message) => (
                <article key={message.message_id}>
                  <span>{message.round_id}</span>
                  <strong>{agentLabel(message.from_agent)} → {agentLabel(message.to_agent)}</strong>
                  <p>{message.content}</p>
                </article>
              ))}
            </div>
            {report.markdown && (
              <details className="rawReport">
                <summary>查看 Markdown 报告</summary>
                <pre>{report.markdown}</pre>
              </details>
            )}
          </>
        ) : (
          <p className="muted">Trace 暂不可用，可能是读取接口失败或本次模拟尚未写入。</p>
        )}
      </section>
    </div>
  );
}

function QualityScoreCard({ score }: { score: QualityScore }) {
  return (
    <article className="qualityCard">
      <div className="qualityHeader">
        <strong>{score.draft_id}</strong>
        <span>{score.final_score.toFixed(2)}</span>
      </div>
      <ScoreBar label="留存" value={score.retention_score} tone="good" />
      <ScoreBar label="好评" value={score.positive_review_score} tone="good" />
      <ScoreBar label="付费" value={score.paid_conversion_score} tone="warn" />
      <ScoreBar label="平台" value={score.platform_recommendation_score} tone="warn" />
      <ScoreBar label="逻辑" value={score.logic_consistency_score ?? 0} tone="good" />
      <ScoreBar label="情绪" value={score.emotional_intensity_score ?? 0} tone="good" />
    </article>
  );
}

function ScoreBar({ label, value, tone }: { label: string; value: number; tone: "good" | "warn" | "risk" }) {
  const width = `${Math.round(clamp(value) * 100)}%`;
  return (
    <div className="scoreBar">
      <div>
        <span>{label}</span>
        <strong>{value.toFixed(2)}</strong>
      </div>
      <div className="barTrack">
        <span className={tone} style={{ width }} />
      </div>
    </div>
  );
}

function InsightCard({ label, value, tone }: { label: string; value: string; tone: "good" | "warn" | "risk" }) {
  return (
    <article className={`insightCard ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function MetricPill({ label, value }: { label: string; value: string }) {
  return (
    <span className="metricPill">
      <small>{label}</small>
      <strong>{value}</strong>
    </span>
  );
}

function SignalList({ title, items }: { title: string; items: string[] }) {
  const unique = uniqueItems(items).slice(0, 4);
  return (
    <div className="signalList">
      <strong>{title}</strong>
      <ul>
        {(unique.length ? unique : ["暂无"]).map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}

function TabButton({
  tab,
  activeTab,
  onClick,
  children
}: {
  tab: TabKey;
  activeTab: TabKey;
  onClick: (tab: TabKey) => void;
  children: React.ReactNode;
}) {
  return (
    <button type="button" className={tab === activeTab ? "active" : ""} onClick={() => onClick(tab)}>
      {children}
    </button>
  );
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function splitList(value: string) {
  return value
    .split(/[、,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function groupBy<T>(items: T[], pickKey: (item: T) => string): Record<string, T[]> {
  return items.reduce<Record<string, T[]>>((acc, item) => {
    const key = pickKey(item);
    acc[key] = acc[key] || [];
    acc[key].push(item);
    return acc;
  }, {});
}

function indexBy<T>(items: T[], pickKey: (item: T) => string): Record<string, T> {
  return items.reduce<Record<string, T>>((acc, item) => {
    acc[pickKey(item)] = item;
    return acc;
  }, {});
}

function avgMetric(items: AudienceJudgment[], key: AudienceMetric): number {
  if (!items.length) return 0;
  return items.reduce((sum, item) => sum + Number(item[key] || 0), 0) / items.length;
}

function collectSignals(items: AudienceJudgment[], key: "trigger_points" | "risk_points"): string[] {
  return items.flatMap((item) => item[key] || []);
}

function uniqueItems(items: string[]): string[] {
  return Array.from(new Set(items.filter(Boolean)));
}

function topEntries(values: Record<string, number>): string[] {
  return Object.entries(values || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([key, value]) => `${key} ${value.toFixed(2)}`);
}

function clamp(value: number): number {
  return Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0));
}

function formatPercent(value: number): string {
  return `${Math.round(clamp(value) * 100)}%`;
}

function readError(reason: unknown): string {
  return reason instanceof Error ? reason.message : String(reason);
}

function agentLabel(agentId: string): string {
  const labels: Record<string, string> = {
    writer: "编剧",
    all: "全体",
    judge: "裁判",
    creative_continuity: "连贯性医生",
    creative_pacing: "节奏医生",
    script_doctor: "剧本医生",
    audience_paid_unlock: "付费观众",
    audience_emotion: "情绪观众",
    audience_shuangwen: "爽文观众",
    platform_distribution: "平台分发",
    paid_unlock: "付费解锁型",
    platform_feed: "平台推荐型",
    emotion_immersive: "情绪沉浸型"
  };
  return labels[agentId] || agentId;
}

createRoot(document.getElementById("root")!).render(<App />);
