# 公网部署：GitHub Pages（前端）+ Render（后端）

可以部署。公开环境只用合成名片数据。

## 架构

```text
浏览器 → GitHub Pages (Vue 静态站)
       → Render (FastAPI + SQLite 种子数据)
       → OpenRouter（大模型，Key 配在 Render 上）
```

## 最省事路线（推荐）

**线上只配一次 Render + GitHub Secret，本地修完 push 就同步，不用每个访客进 Settings 填 Key。**

| 环境 | 你要配什么 |
|------|------------|
| **Render（后端）** | `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL` |
| **GitHub Secret** | `VITE_API_BASE` = Render API 地址 |
| **本地开发** | 浏览器 Settings：后端 `http://127.0.0.1:8000` + OpenRouter Key（或 backend/.env） |

### Render 环境变量（Dashboard → cardledger-api → Environment）

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | 在 [openrouter.ai/keys](https://openrouter.ai/keys) 创建 |
| `OPENAI_BASE_URL` | `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | 例如 `google/gemma-2-9b-it:free` |

`render.yaml` 已写好 `BASE_URL` 和默认模型；**只需在 Render 填 Key**（sync: false，不会进 Git）。

填完后在 Render 打开 `https://你的-api.onrender.com/health` — `has_llm` 应为 `true`。  
再测 `https://你的-api.onrender.com/health/llm-test` — 应返回 `{"ok":true,...}`。

### GitHub Pages

1. Settings → Secrets → Actions → `VITE_API_BASE` = `https://你的-render-api.onrender.com`
2. 推送到 `main`，workflow 自动发布

访客打开 Pages 站点即可用；**不必**再进 Settings 填 Key（除非想用自己的 Key 覆盖）。

---

## 本地 ↔ 线上同步流程

```bash
# 1. 本地改代码、跑通
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev

# 2. Settings 里测「测试后端」「测试大模型」都 OK

# 3. 提交并推送 — Render 和 Pages 会自动 redeploy
git add -A && git commit -m "..." && git push origin main
```

本地 Settings 里的 Key **不会**跟着 push 走；线上靠 Render 环境变量。  
本地若不想每次开 Settings，可在项目根 `.env` 写同样的 `OPENAI_*`（见 `.env.example`）。

---

## Settings 页两个 URL 别搞混

| 字段 | 填什么 | 常见误填 |
|------|--------|----------|
| **后端 API 地址** | `http://127.0.0.1:8000` 或 Render URL | ❌ 填成 openrouter.ai |
| **大模型 Base URL** | `https://openrouter.ai/api/v1` | ❌ 填成 127.0.0.1:8000 |

点 **「一键填入 OpenRouter 预设」** 可自动填大模型地址和免费模型名。

---

## 1. 建 GitHub 仓库并推送

本项目需单独仓库（不要挂在家目录大仓库上）。

## 2. Render 部署后端

1. [Render Dashboard](https://dashboard.render.com) → New → Blueprint
2. 连接本仓库，使用根目录 [`render.yaml`](../render.yaml)
3. 在 Environment 填入 `OPENAI_API_KEY`
4. 记下 API 地址，例如 `https://cardledger-api.onrender.com`

冷启动免费实例会睡，第一次打开可能要等 30–60 秒。

## 3. GitHub Pages 部署前端

1. 仓库 Settings → Pages → Source: **GitHub Actions**
2. Secret `VITE_API_BASE` = Render API 地址（无末尾斜杠）
3. 推送 `main` 后 [deploy-pages.yml](../.github/workflows/deploy-pages.yml) 自动构建

站点：`https://<user>.github.io/<repo>/`

## 4. CORS

`render.yaml` 默认 `CORS_ORIGINS=*` 方便联调。上线后可改成你的 Pages 域名。

## 扫描录入 vs 问答

- **扫描**：需要 LLM 做 JSON 结构化抽取；免费模型可能不支持 `json_mode`，后端会自动降级重试。
- **问答**：普通聊天即可，所以同一模型在 Ask 里往往更「通人性」。
- 若扫描失败，界面会提示 **手动填写**，不再把 OCR 第一行当姓名乱填。
- Settings → **测试大模型** 比「测试后端」更能确认 Key 真的可用。

## 注意

- 公网只放合成数据；真实名片走私有/本地
- OCR 依赖较重，Render 免费版构建可能较慢
- SQLite 无持久盘时，重启会重新 seed（演示可接受）
