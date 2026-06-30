from __future__ import annotations

import json
from pathlib import Path

from config.settings import settings
from schemas.trace import TraceRecord


def save_trace(record: TraceRecord) -> Path:
    trace_dir = _trace_dir()
    trace_dir.mkdir(parents=True, exist_ok=True)
    path = trace_dir / f"{record.simulation_id}.json"
    path.write_text(
        json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def list_traces() -> list[dict]:
    trace_dir = _trace_dir()
    trace_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(trace_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        rows.append(
            {
                "simulation_id": data.get("simulation_id", path.stem),
                "created_at": data.get("created_at"),
                "title": data.get("input", {}).get("title"),
                "recommended_draft_id": data.get("final_report", {}).get("recommended_draft_id"),
                "path": str(path),
            }
        )
    return rows


def get_trace(simulation_id: str) -> dict | None:
    path = _trace_dir() / f"{simulation_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _trace_dir() -> Path:
    trace_dir = Path(settings.trace_dir)
    if not trace_dir.is_absolute():
        trace_dir = Path(__file__).resolve().parents[2] / trace_dir
    return trace_dir
