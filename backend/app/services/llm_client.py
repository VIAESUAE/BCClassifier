from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import httpx

from app.services.llm_runtime import effective_api_key, effective_base_url, effective_model


def llm_headers() -> Dict[str, str]:
    headers = {
        "Authorization": f"Bearer {effective_api_key()}",
        "Content-Type": "application/json",
    }
    if "openrouter.ai" in effective_base_url():
        headers["HTTP-Referer"] = "https://cardledger.app"
        headers["X-Title"] = "CardLedger"
    return headers


def chat_completion(
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0,
    json_mode: bool = False,
) -> str:
    body: Dict[str, Any] = {
        "model": effective_model(),
        "temperature": temperature,
        "messages": messages,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    with httpx.Client(base_url=effective_base_url(), timeout=90.0) as client:
        resp = client.post("/chat/completions", headers=llm_headers(), json=body)
        if json_mode and resp.status_code in (400, 422):
            # OpenRouter free models often reject response_format — retry plain.
            body.pop("response_format", None)
            resp = client.post("/chat/completions", headers=llm_headers(), json=body)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


def parse_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def ping_llm() -> str:
    content = chat_completion(
        [
            {"role": "user", "content": 'Reply with exactly: {"ok":true}'},
        ],
        temperature=0,
        json_mode=False,
    )
    return content[:240]
