# Drama Smallville P0 Backend

P0 implementation for the author-driven AI virtual screening room.

## What Works

- `POST /api/drama/demo-run`
- Story material normalization into `StoryWorldState`
- Candidate draft generation
- Creative review with continuity and pacing advisors
- Audience/platform simulation with round-1 and round-2 revision
- Critic challenge
- Draft quality scoring
- Structured report generation
- JSON trace persistence
- Mock/heuristic fallback without model API keys
- P1 population fitting APIs:
  - `GET /api/population/profile-set`
  - `GET /api/population/fit-report`
- Trace APIs:
  - `GET /api/traces`
  - `GET /api/traces/{simulation_id}`
- Agent memory APIs:
  - `GET /api/agents/{agent_id}/memory`
  - `POST /api/agents/{agent_id}/memory/patterns`

## Prerequisites

- Python 3.13+
- 依赖见 `requirements.txt`：fastapi / uvicorn / pydantic / httpx / numpy / scikit-learn / pytest
- 首次运行建议建虚拟环境：`python3 -m venv .venv && source .venv/bin/activate`（macOS/Linux）
- `scikit-learn` 不可用时 `compressor.py` 自动降级到规则桶分配（见 ADR-0003），但 KMeans 真路径需装齐
- 跑测试：`cd "script simulation/backend" && python -m pytest tests/ -v`

## Run

```bash
cd "script simulation/backend"
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Demo endpoint:

```bash
curl -X POST http://127.0.0.1:8000/api/drama/demo-run \
  -H 'Content-Type: application/json' \
  -d @sample_request.json
```

Simple text endpoint:

```bash
curl -X POST http://127.0.0.1:8000/api/drama/simple-run \
  -H 'Content-Type: application/json' \
  -d '{"title":"测试","text":"女主发现男主隐瞒真相，但真正幕后黑手是养父。","platform_type":"wechat_minidrama","business_goal":"paid_conversion"}'
```

Population fit:

```bash
curl "http://127.0.0.1:8000/api/population/fit-report?platform_type=wechat_minidrama&business_goal=paid_conversion&max_agents=6"
```

## Notes

- P0 scores are heuristic and not real market predictions.
- Model routing is represented by `llm/gateway.py`; P0 uses deterministic fallback logic for stability.
- Traces are saved under `backend/storage/traces/`.
- Agent memory files are reserved under `backend/storage/agent_memory/`.
