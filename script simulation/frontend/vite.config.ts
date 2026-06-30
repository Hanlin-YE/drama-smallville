import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 开发模式:vite dev (5173) 通过 proxy 把 /api/* 转发到后端 (8000),
// 前端用同源相对路径 fetch('/api/...') 即可,不依赖 CORS,不硬编码端口。
// 生产模式:backend 用 StaticFiles 挂载 frontend/dist,单端口同源。
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
