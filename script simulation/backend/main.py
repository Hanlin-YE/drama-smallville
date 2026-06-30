from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from api.drama_routes import router as drama_router
from api.memory_routes import router as memory_router
from api.population_routes import router as population_router
from api.trace_routes import router as trace_router

app = FastAPI(title="Drama Smallville P0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(drama_router)
app.include_router(population_router)
app.include_router(trace_router)
app.include_router(memory_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")
