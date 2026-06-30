# 前后端集成模式:dev proxy + prod 同源 serve

## 上下文

项目有三个"前端":
- `script simulation/frontend/` — React 19 + Vite 7 应用,31KB main.tsx,已 fetch 后端 4 个端点(simple-run / population / traces / memory)。是真正的应用前端。
- `script simulation/backend/static/index.html` — 13KB 旧版静态页,被 backend `/` 路由返回。P0 早期的单文件 UI。
- `ui-demo/writers-room-demo.html` — 29KB 纯静态设计稿,零 fetch,不与后端通信。是设计参考。

## 决定

1. **`frontend/` 是唯一的应用前端**。`backend/static/index.html` 降级为开发模式 fallback(当 frontend/dist 不存在时)。`ui-demo/` 定位为设计稿存档,不参与运行。
2. **开发模式**:vite dev (5173) + backend (8000) 双进程,vite proxy 把 `/api/*` 和 `/health` 转发到后端。前端用同源相对路径 `fetch('/api/...')`,不硬编码端口,不依赖 CORS。
3. **生产模式**:`cd frontend && npm run build` 后,backend 用 StaticFiles 挂载 `frontend/dist`,单端口 8000 同源 serve 前端 + API。

## 理由

1. **dev proxy 消除 CORS 依赖**:原来 frontend 硬编码 `API_BASE = "http://127.0.0.1:8000"`,靠 backend `allow_origins=["*"]` 跨域。开发时没问题,但生产不该开 CORS 全放。proxy 让 dev 时同源,prod 时 backend 直接 serve dist 也同源,两个模式都不需要 CORS。
2. **单端口生产部署更简单**:不用同时管前端 server 和后端 server,一个 `uvicorn main:app` 全搞定。SPA 的 `/assets/*` 由 StaticFiles 挂载,`/` 返回 dist/index.html。
3. **保留 backend/static 作 fallback**:开发时若只起 backend 不起 vite,`/` 仍返回旧版页,不会白屏。这让 backend 独立可跑(测试、CI)。

## 后果

- `frontend/dist/` 在 `.gitignore` 里(构建产物不入库),生产部署需先 `npm run build`。
- backend `/` 路由有优先级逻辑:dist 存在则 serve dist,否则 serve static。这个逻辑在 main.py 里,测试覆盖见 test_api.py::test_index_returns_html。
- CORS 中间件仍保留(开发时 vite 5173 直连后端 8000 的场景需要),但生产同源时不触发。
- `ui-demo/` 保留作设计参考,不删——它是 writers-room 交互的原始设计稿,frontend 的 Tab 布局源自它。

## 更正

grill 报告(2026-06-30)第 5 维度曾说"frontend 是 Vite+React 空壳(src 仅 main.tsx+styles.css,无 tsconfig),且零 fetch,不与后端通信"。这是严重误判——实际 main.tsx 有 31KB、已 fetch 4 个后端端点、有完整 Tab 布局和报告渲染。误判原因:只看了文件列表和无 tsconfig,没读 main.tsx 内容。这印证了 grill 报告自己的教训:"每个判断都要用能跑的动作证伪一次。"
