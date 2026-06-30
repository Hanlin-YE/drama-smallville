"""API 层端到端测试。

底层管线已有 tests/test_pipeline.py 覆盖;本文件补 API 层断层——
用 TestClient 穿过 FastAPI 路由 → 业务逻辑 → 存储,验证 8 个端点
的 happy path。这正是 grill 报告指出的"底层有测试、API 层裸奔"缺口。

设计原则(grill §6 可测试性):
- 穿过 seam 测:TestClient 打真实 HTTP,不断言内部状态
- 依赖真实 trace 目录(已存在历史 trace),不 mock 存储
- simple-run 走完整 run_demo,验证编排链路通
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ── 基础端点 ──────────────────────────────────────────────────────────────────


class TestHealthAndIndex:
    def test_health_returns_ok(self, client: TestClient) -> None:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_index_returns_html(self, client: TestClient) -> None:
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        # 静态页应有可识别内容,不是空壳
        assert len(r.text) > 200


# ── Population 端点 ───────────────────────────────────────────────────────────


class TestPopulationRoutes:
    def test_profile_set_returns_agents(self, client: TestClient) -> None:
        r = client.get("/api/population/profile-set", params={"seed": 42, "max_agents": 4})
        assert r.status_code == 200
        data = r.json()
        assert "representative_agents" in data
        assert len(data["representative_agents"]) <= 4
        # 每个 agent 必须有 evidence(grill §4 深模块:compressor 契约)
        for agent in data["representative_agents"]:
            assert "agent_id" in agent
            assert "evidence" in agent

    def test_profile_set_seed_reproducible(self, client: TestClient) -> None:
        r1 = client.get("/api/population/profile-set", params={"seed": 7})
        r2 = client.get("/api/population/profile-set", params={"seed": 7})
        assert r1.status_code == 200 and r2.status_code == 200
        a1 = [a["agent_id"] for a in r1.json()["representative_agents"]]
        a2 = [a["agent_id"] for a in r2.json()["representative_agents"]]
        assert a1 == a2

    def test_fit_report_returns_population_fit(self, client: TestClient) -> None:
        r = client.get("/api/population/fit-report", params={"seed": 42})
        assert r.status_code == 200
        data = r.json()
        assert "max_feature_error" in data
        assert "accepted" in data


# ── Drama 端点 ────────────────────────────────────────────────────────────────


class TestDramaRoutes:
    def test_simple_run_returns_report(self, client: TestClient) -> None:
        r = client.post(
            "/api/drama/simple-run",
            json={
                "text": "女主发现男主隐瞒真相,但真正幕后黑手是养父。女主假意合作暗中设局反杀。",
                "title": "反杀局",
                "platform_type": "wechat_minidrama",
                "business_goal": "paid_conversion",
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # StorySimulationReport 契约(见 schemas/report.py)
        assert "simulation_id" in data
        assert "candidate_drafts" in data
        assert isinstance(data["candidate_drafts"], list)
        assert len(data["candidate_drafts"]) > 0
        assert "recommended_draft_id" in data
        assert "confidence_level" in data
        # 至少有一个候选应有 draft_id
        first = data["candidate_drafts"][0]
        assert "draft_id" in first


# ── Trace 端点 ────────────────────────────────────────────────────────────────


class TestTraceRoutes:
    def test_list_traces_returns_list(self, client: TestClient) -> None:
        r = client.get("/api/traces")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # 历史已有 trace,列表应非空
        if data:
            row = data[0]
            assert "simulation_id" in row
            assert "created_at" in row

    def test_get_trace_by_id_returns_full_or_404(self, client: TestClient) -> None:
        # 先拿列表取一个真实 id
        listing = client.get("/api/traces").json()
        if not listing:
            pytest.skip("无历史 trace,跳过单条回放测试")
        sim_id = listing[0]["simulation_id"]
        r = client.get(f"/api/traces/{sim_id}")
        assert r.status_code == 200
        data = r.json()
        assert data.get("simulation_id") == sim_id

    def test_get_trace_unknown_id_returns_404(self, client: TestClient) -> None:
        r = client.get("/api/traces/definitely_does_not_exist_12345")
        assert r.status_code == 404


# ── Agent Memory 端点 ─────────────────────────────────────────────────────────


class TestMemoryRoutes:
    def test_get_memory_for_unknown_agent_returns_default(self, client: TestClient) -> None:
        r = client.get("/api/agents/test_api_probe_unknown/memory")
        assert r.status_code == 200
        data = r.json()
        # memory_store 对未知 agent 返回默认结构
        assert data.get("agent_id") == "test_api_probe_unknown"
        assert "learned_patterns" in data

    def test_add_pattern_persists(self, client: TestClient) -> None:
        agent_id = "test_api_probe_pattern"
        r = client.post(
            f"/api/agents/{agent_id}/memory/patterns",
            json={
                "description": "测试用 pattern:高冲突场景下付费意愿上升",
                "applies_to_platforms": ["wechat_minidrama"],
                "signal": "strong_conflict",
                "expected_metric_effect": {"pay": 0.05},
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert any(p["description"] == "测试用 pattern:高冲突场景下付费意愿上升" for p in data["learned_patterns"])
        # 回读确认持久化
        r2 = client.get(f"/api/agents/{agent_id}/memory")
        assert r2.status_code == 200
        assert len(r2.json()["learned_patterns"]) >= 1
