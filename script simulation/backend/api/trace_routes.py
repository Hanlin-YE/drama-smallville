from __future__ import annotations

from fastapi import APIRouter, HTTPException

from storage.trace_store import get_trace, list_traces

router = APIRouter(prefix="/api/traces", tags=["traces"])


@router.get("")
def traces() -> list[dict]:
    return list_traces()


@router.get("/{simulation_id}")
def trace(simulation_id: str) -> dict:
    data = get_trace(simulation_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return data

