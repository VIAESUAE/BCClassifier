# 公网部署：GitHub Pages（前端）+ Render（后端）

可以部署。公开环境只用合成名片数据。

## 架构

```text
浏览器 → GitHub Pages (Vue 静态站)
       → Render (FastAPI + SQLite 种子数据)
```

设置页里也能手动改 API 地址 / API Key。

## 1. 先建独立 GitHub 仓库并推送

本项目目录需要单独 `git init`（不要挂在家目录大仓库上）。

## 2. Render 部署后端

1. [Render Dashboard](https://dashboard.render.com) → New → Blueprint / Web Service
2. 连接本仓库，使用根目录 [`render.yaml`](../render.yaml)
3. 或手动：
   - Root Directory: `backend`
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. 记下 API 地址，例如 `https://cardledger-api.onrender.com`
5. 可选：在 Render 填 `OPENAI_API_KEY`（不填也能离线演示）

冷启动免费实例会睡，第一次打开可能要等 30–60 秒。

## 3. GitHub Pages 部署前端

1. 仓库 Settings → Pages → Source: **GitHub Actions**
2. 仓库 Settings → Secrets → Actions，新增：
   - Name: `VITE_API_BASE`
   - Value: `https://你的-render-api.onrender.com`（不要末尾斜杠）
3. 推送到 `main` 后，workflow [`deploy-pages.yml`](../.github/workflows/deploy-pages.yml) 会自动构建发布
4. 站点：`https://<user>.github.io/<repo>/`

## 4. CORS

`render.yaml` 默认 `CORS_ORIGINS=*` 方便联调。上线后可改成你的 Pages 域名。

## 注意

- 公网只放合成数据；真实名片走私有/本地
- OCR 依赖较重，Render 免费版构建可能较慢
- SQLite 无持久盘时，重启会重新 seed（演示可接受）
