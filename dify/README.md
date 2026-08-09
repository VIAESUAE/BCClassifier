# Dify thin integration (platform signal only)

Core retrieval stays in this repo (`POST /rag/query`). Dify is an optional shell so you can
show platform familiarity without depending on it.

## Setup

1. Run CardLedger API locally or on a private host (`http://localhost:8000`).
2. In Dify: create a **Chatflow** or **Workflow**.
3. Add an **HTTP Request** node:
   - Method: `POST`
   - URL: `http://host.docker.internal:8000/rag/query` (Mac Docker Desktop) or your API URL
   - Headers: `Content-Type: application/json`
   - Body:

```json
{
  "query": "{{#sys.query#}}",
  "top_k": 5
}
```

4. Add an LLM / answer node that formats `answer` + `hits` from the HTTP response.
   Prefer quoting the API `answer` field directly so grounding stays in your backend.

## Import

Use [chatflow_rag_proxy.yml](chatflow_rag_proxy.yml) as a starting template (adjust URL for your environment).

## Resume wording

> Integrated Dify Chatflow with a self-hosted hybrid RAG API over structured business-card records (PostgreSQL + embeddings). Platform used for orchestration only; retrieval logic owned in-house.

## Security

Point Dify only at **synthetic demo** backends for anything reachable outside your LAN.
