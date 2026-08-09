#!/usr/bin/env bash
# Smoke test for CardLedger API (expects API on :8000)
set -euo pipefail
BASE="${1:-http://127.0.0.1:8000}"

echo "== health =="
curl -sf "$BASE/health" | python3 -m json.tool

echo "== rag (main story) =="
curl -sf -X POST "$BASE/rag/query" \
  -H 'Content-Type: application/json' \
  -d '{"query":"美国西海岸搞支付或者资金搭桥的人","top_k":3}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'][:400]); print('hits', [h['card']['full_name'] for h in d['hits']])"

echo "== cards =="
curl -sf "$BASE/cards" | python3 -c "import sys,json; print(len(json.load(sys.stdin)), 'cards')"

echo "OK"
