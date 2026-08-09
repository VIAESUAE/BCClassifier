from __future__ import annotations

import json
import re
from typing import List, Tuple

import httpx

from app.schemas import CardFields
from app.services.geo import enrich_card_geo
from app.services.llm_runtime import effective_api_key, effective_base_url, effective_model, has_llm

EXTRACT_SYSTEM = """You extract structured fields from business card OCR text.
Return ONLY valid JSON matching this schema:
{
  "full_name": string,
  "company": string|null,
  "title": string|null,
  "phone": string|null,
  "email": string|null,
  "country": string|null,
  "timezone": string|null,
  "region": string|null,
  "geo_zone": "APAC"|"NA"|"LATAM"|"EU"|"MEA"|null,
  "tags": string[],
  "notes": string|null
}
Rules:
- Infer country from address, city, or phone country code when possible.
- timezone MUST be an IANA name when known (e.g. Asia/Singapore, America/New_York, Europe/London).
- region: city or metro label (e.g. "Bay Area", "New York", "Singapore").
- geo_zone: classify from address/country into exactly one of:
  APAC (Asia-Pacific), NA (North America), LATAM (Latin America), EU (Europe), MEA (Middle East & Africa).
- tags: short industry labels like "payments", "fintech", "cloud services", "hardware", "legal", "retail", "logistics".
- If unsure, use null / []. Do not invent phone/email.
"""


def extract_fields(ocr_text: str) -> Tuple[CardFields, List[str]]:
    warnings: List[str] = []
    if has_llm() and ocr_text.strip():
        try:
            fields = _llm_extract(ocr_text)
            return _finalize(fields, ocr_text), warnings
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"LLM extract failed, using heuristics: {exc}")
    fields = _heuristic_extract(ocr_text)
    if not fields.full_name:
        warnings.append("Could not confidently detect a name; please edit before saving.")
    return _finalize(fields, ocr_text), warnings


def _finalize(fields: CardFields, ocr_text: str) -> CardFields:
    country, timezone, geo_zone, city = enrich_card_geo(
        ocr_text=ocr_text,
        phone=fields.phone,
        country=fields.country,
        region=fields.region,
        timezone=fields.timezone,
        geo_zone=fields.geo_zone,
    )
    region = fields.region or city
    return fields.model_copy(
        update={
            "country": country,
            "timezone": timezone,
            "geo_zone": geo_zone,
            "region": region,
        }
    )


def _llm_extract(ocr_text: str) -> CardFields:
    payload = {
        "model": effective_model(),
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": f"OCR text:\n{ocr_text}"},
        ],
    }
    headers = {
        "Authorization": f"Bearer {effective_api_key()}",
        "Content-Type": "application/json",
    }
    with httpx.Client(base_url=effective_base_url(), timeout=60.0) as client:
        resp = client.post("/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
    data = json.loads(content)
    return CardFields.model_validate(data)


def _heuristic_extract(ocr_text: str) -> CardFields:
    lines = [ln.strip() for ln in ocr_text.splitlines() if ln.strip()]
    email = None
    phone = None
    for ln in lines:
        if not email:
            m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", ln)
            if m:
                email = m.group(0)
        if not phone:
            m = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", ln)
            if m and "@" not in ln:
                phone = m.group(0).strip()

    full_name = lines[0] if lines else "Unknown"
    company = None
    title = None
    for ln in lines[1:6]:
        lower = ln.lower()
        if email and email in ln:
            continue
        if phone and phone in ln:
            continue
        if any(k in lower for k in ("inc", "llc", "corp", "ltd", "labs", "capital", "pay", "bank")):
            company = company or ln
        elif any(k in lower for k in ("ceo", "cto", "vp", "director", "manager", "partner", "engineer", "founder")):
            title = title or ln
        elif company is None and "@" not in ln:
            company = ln

    blob = ocr_text.lower()
    tags: List[str] = []
    tag_map = {
        "payment": "payments",
        "payments": "payments",
        "fintech": "fintech",
        "fund": "fund bridging",
        "bridge": "fund bridging",
        "venture": "venture capital",
        "crypto": "crypto",
        "bank": "banking",
        "cloud": "cloud services",
        "aws": "cloud services",
        "azure": "cloud services",
        "hardware": "hardware",
        "semiconductor": "hardware",
        "legal": "legal",
        "law": "legal",
        "retail": "retail",
        "logistics": "logistics",
        "shipping": "logistics",
    }
    for key, tag in tag_map.items():
        if key in blob and tag not in tags:
            tags.append(tag)

    return CardFields(
        full_name=full_name[:255],
        company=company,
        title=title,
        phone=phone,
        email=email,
        country=None,
        timezone=None,
        region=None,
        geo_zone=None,
        tags=tags,
        notes=None,
    )


def build_embedding_text(fields: CardFields) -> str:
    parts = [
        fields.full_name,
        fields.company or "",
        fields.title or "",
        fields.country or "",
        fields.region or "",
        fields.geo_zone or "",
        fields.timezone or "",
        " ".join(fields.tags or []),
        fields.notes or "",
    ]
    return " | ".join(p for p in parts if p).strip()
