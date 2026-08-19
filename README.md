# CardLedger — Business Card Knowledge Base (RAG)

Scan or photograph a business card → preprocess → OCR → structured extract → PostgreSQL + embeddings → **hybrid RAG** (semantic + region/timezone/tags).

**Primary story for resumes:** leadership can ask *“美国西海岸搞支付或者资金搭桥的人”* and get grounded contacts.

> **Demo data — synthetic only.** Public deployments must never store real business cards. Real contacts belong on private / local Docker.

## Why this project

| Goal | How it’s shown |
|------|----------------|
| RAG for AI-app intern roles | Hybrid retrieve + grounded answer on `/rag/query` |
| Vision / Document AI | OpenCV preprocess + RapidOCR + LLM/heuristic schema extract |
| Database | PostgreSQL + pgvector (Docker); SQLite fallback for laptop smoke tests |
| Vue3 engineering / UX | Guided ingest wizard + plain-language search |
| Platform familiarity | Thin [Dify](dify/README.md) Chatflow that calls your API |

## Quick start (local, no Docker)

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # optional; defaults to sqlite:///./cardrag.db
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — seed contacts load automatically (West Coast payments / fund bridging + East Coast decoys).

### Main story query

Use **Ask** with:

`美国西海岸搞支付或者资金搭桥的人`

or

`Who on the US West Coast works on payments or fund bridging?`

## Docker (recommended private / Postgres+pgvector)

```bash
cp .env.example .env   # add OPENAI_API_KEY if you want LLM extract + answers
docker compose up --build
```

- UI: http://localhost:8080  
- API: http://localhost:8000/docs  

## Synthetic printables for OCR practice

```bash
# from repo root, with backend venv active (needs Pillow)
python scripts/generate_synthetic_cards.py
```

Print PNGs under `data/synthetic/`, photograph/scan them, then use **Scan in**.

## Architecture

```text
Vue3 UI ──▶ FastAPI
              ├─ /ingest/preview  OpenCV → OCR → extract
              ├─ /ingest/confirm  PostgreSQL + embedding
              └─ /rag/query       hybrid filters + vector score + answer
```

Optional: Dify HTTP node → same `/rag/query` ([dify/](dify/)).

## Data classification

| Mode | Data | Deploy |
|------|------|--------|
| Public demo | Synthetic seed + fake printed cards | Render / Pages OK (`render.yaml`) |
| Private use | Real cards (if ever) | Local Docker / intranet only |

## API sketch

- `GET /health`
- `POST /ingest/preview` multipart file
- `POST /ingest/confirm` JSON `{ preview_id, fields }`
- `POST /rag/query` JSON `{ query, top_k }`
- `GET /cards`

## Env

See [.env.example](.env.example). Without `OPENAI_API_KEY`, heuristic extract + deterministic hash embeddings still run the demo end-to-end.

**OpenRouter (free models):** set `OPENAI_BASE_URL=https://openrouter.ai/api/v1` and a model like `google/gemma-2-9b-it:free`. In the UI **Settings**, use **Test LLM** — not just health — before scanning cards.

## Public deploy (GitHub Pages + Render)

Push to `main` redeploys both. Configure once on Render:

- `OPENAI_API_KEY` — from [openrouter.ai/keys](https://openrouter.ai/keys)
- `OPENAI_BASE_URL` — `https://openrouter.ai/api/v1` (already in `render.yaml`)
- GitHub Secret `VITE_API_BASE` — your Render API URL

Full checklist: [scripts/PUBLIC_DEMO.md](scripts/PUBLIC_DEMO.md). **Do not** put the backend URL (`127.0.0.1:8000`) in the LLM Base URL field.

Never upload real business cards to the public stack.
