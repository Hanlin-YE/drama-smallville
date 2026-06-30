from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MEMORY_DIR = Path(__file__).resolve().parents[1] / "storage" / "agent_memory"


def get_memory(agent_id: str) -> dict[str, Any]:
    path = MEMORY_DIR / f"{agent_id}.json"
    if not path.exists():
        return _default_memory(agent_id)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _default_memory(agent_id)


def append_pattern(agent_id: str, pattern: dict[str, Any]) -> dict[str, Any]:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    memory = get_memory(agent_id)
    memory.setdefault("learned_patterns", []).append(pattern)
    memory["agent_id"] = agent_id
    path = MEMORY_DIR / f"{agent_id}.json"
    path.write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")
    return memory


def _default_memory(agent_id: str) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "memory_version": "v1",
        "learned_patterns": [],
        "calibration_notes": [],
        "confidence": 0.5,
    }

