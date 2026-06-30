from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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


# 前端集成:生产模式优先 serve frontend/dist(单端口同源),
# 开发模式(vite dev 在 5173)fallback 到 backend/static 旧版页。
# 详见 docs/adr/0006-frontend-integration.md
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"
BACKEND_STATIC = BACKEND_DIR / "static"


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    dist_index = FRONTEND_DIST / "index.html"
    if dist_index.exists():
        return dist_index.read_text(encoding="utf-8")
    return (BACKEND_STATIC / "index.html").read_text(encoding="utf-8")


# 挂载 frontend/dist 的静态资源(/assets/*),生产模式 SPA 所需。
# 若 dist 不存在(纯开发模式),跳过挂载——前端由 vite dev server 提供。
if FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="frontend-assets",
    )
