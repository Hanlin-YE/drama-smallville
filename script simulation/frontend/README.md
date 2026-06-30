# Drama Smallville Frontend

React 19 + Vite 7 + TypeScript 应用。短剧虚拟试播台的前端界面。

## 开发模式

需要后端跑在 8000(见 `../backend/README.md`)。

```bash
cd "script simulation/frontend"
npm install
npm run dev
```

打开 http://127.0.0.1:5173 。vite proxy 会把 `/api/*` 和 `/health` 转发到后端 8000,前端用同源相对路径,不依赖 CORS。

## 生产模式

```bash
npm run build        # 产出 dist/
cd ../backend
python -m uvicorn main:app --port 8000
```

backend 会自动检测 `frontend/dist/` 并挂载为静态资源,单端口 8000 同源 serve 前端 + API。打开 http://127.0.0.1:8000 。

## 架构

- `src/main.tsx` — 单文件应用(31KB):状态管理、API 调用、Tab 布局、报告渲染
- `src/styles.css` — 样式
- `vite.config.ts` — vite 配置 + dev proxy
- `tsconfig.json` — TypeScript 配置

前端调用后端 4 个端点:
- `POST /api/drama/simple-run` — 试播,返回 StorySimulationReport
- `GET /api/population/profile-set` — 观众群 profile
- `GET /api/traces/{id}` — 试播 trace 回放
- `GET /api/agents/screenwriter/memory` — 编剧记忆

集成模式决策见 `docs/adr/0006-frontend-integration.md`。
