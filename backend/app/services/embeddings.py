from __future__ import annotations

import hashlib
import math
from typing import List

import httpx
import numpy as np

from app.config import get_settings
from app.services.llm_runtime import effective_api_key, effective_base_url, has_llm


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    settings = get_settings()
    if has_llm():
        try:
            return _openai_embed(texts)
        except Exception:
            return [_fallback_embed(t, settings.embedding_dim) for t in texts]
    return [_fallback_embed(t, settings.embedding_dim) for t in texts]


def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]


def _openai_embed(texts: List[str]) -> List[List[float]]:
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {effective_api_key()}",
        "Content-Type": "application/json",
    }
    payload = {"model": settings.embedding_model, "input": texts}
    with httpx.Client(base_url=effective_base_url(), timeout=60.0) as client:
        resp = client.post("/embeddings", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()["data"]
        data = sorted(data, key=lambda x: x["index"])
        return [row["embedding"] for row in data]


def _fallback_embed(text: str, dim: int) -> List[float]:
    """Deterministic bag-of-hashes embedding for offline / no-key demos."""
    vec = np.zeros(dim, dtype=np.float64)
    tokens = [t for t in text.lower().replace("|", " ").split() if t]
    if not tokens:
        tokens = ["empty"]
    for tok in tokens:
        digest = hashlib.sha256(tok.encode("utf-8")).digest()
        for i in range(0, min(len(digest), 32)):
            idx = (digest[i] * 17 + i * 31 + len(tok)) % dim
            sign = 1.0 if digest[i] % 2 == 0 else -1.0
            vec[idx] += sign
    norm = math.sqrt(float(np.dot(vec, vec))) or 1.0
    vec = vec / norm
    return vec.astype(float).tolist()
