from __future__ import annotations

import re
from typing import List, Tuple

import httpx

from app.schemas import CardFields
from app.services.geo import enrich_card_geo
from app.services.llm_client import chat_completion, parse_json_object
from app.services.llm_runtime import has_llm

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
- Ignore marketing slogans, taglines, and calls-to-action (e.g. "In Legal Trouble?", "Call Now!", "Better Call Saul!").
- full_name must be a person's name (e.g. "Saul Goodman"), NOT a slogan or question.
- company is an organization name, NOT a catchphrase.
- title is a job title (e.g. "Attorney at Law", "VP Sales"), not advertising copy.
- Prefer lines that look like contact info; skip decorative or promotional text.
- Infer country from address, city, or phone country code when possible.
- timezone: IANA name when known (e.g. America/Los_Angeles, Asia/Singapore).
- geo_zone: APAC | NA | LATAM | EU | MEA from address/country.
- tags: short industry labels (payments, legal, cloud services, retail, etc.).
- If unsure, use null / []. Do not invent phone/email.
"""


def extract_fields(ocr_text: str) -> Tuple[CardFields, List[str]]:
    warnings: List[str] = []
    if has_llm() and ocr_text.strip():
        try:
            fields = _llm_extract(ocr_text)
            return _finalize(fields, ocr_text), warnings
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            detail = exc.response.text[:300]
            warnings.append(f"LLM API error {code}: {detail}")
            if code in (401, 403):
                warnings.append(
                    "API Key 未授权。OpenRouter 请确认：Base URL = https://openrouter.ai/api/v1，"
                    "Key 来自 openrouter.ai，模型名如 google/gemma-2-9b-it:free"
                )
            warnings.append("未能自动抽取字段，请根据 OCR 文本手动填写（未使用离线规则乱填）。")
            return _finalize(_empty_fields(), ocr_text), warnings
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"LLM extract failed: {exc}")
            warnings.append("请手动填写字段，或到「设置」检查 OpenRouter 配置。")
            return _finalize(_empty_fields(), ocr_text), warnings

    fields = _heuristic_extract(ocr_text)
    warnings.append("未配置 LLM Key，使用离线规则抽取（精度有限，建议到「设置」填入 OpenRouter）。")
    if not fields.full_name or fields.full_name == "待手动填写":
        warnings.append("Could not confidently detect a name; please edit before saving.")
    return _finalize(fields, ocr_text), warnings


def _empty_fields() -> CardFields:
    return CardFields(
        full_name="待手动填写",
        company=None,
        title=None,
        phone=None,
        email=None,
        country=None,
        timezone=None,
        region=None,
        geo_zone=None,
        tags=[],
        notes=None,
    )


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
    messages = [
        {"role": "system", "content": EXTRACT_SYSTEM},
        {"role": "user", "content": f"OCR text:\n{ocr_text}"},
    ]
    try:
        content = chat_completion(messages, temperature=0, json_mode=True)
    except httpx.HTTPStatusError:
        raise
    except Exception:
        content = chat_completion(messages, temperature=0, json_mode=False)
    data = parse_json_object(content)
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

    # Skip obvious slogans for name guess
    def looks_like_name(ln: str) -> bool:
        if "?" in ln or "!" in ln and len(ln.split()) <= 4:
            return False
        if ln.isupper() and len(ln) > 28:
            return False
        words = ln.split()
        return 2 <= len(words) <= 4 and not any(w.lower() in ("call", "better", "now") for w in words[:1])

    full_name = "待手动填写"
    for ln in lines[:8]:
        if looks_like_name(ln):
            full_name = ln
            break
    if full_name == "待手动填写" and lines:
        full_name = lines[0][:255]

    company = None
    title = None
    for ln in lines:
        lower = ln.lower()
        if email and email in ln:
            continue
        if phone and phone in ln:
            continue
        if any(k in lower for k in ("attorney", "lawyer", "ceo", "cto", "vp", "director", "manager", "partner", "engineer", "founder", "at law")):
            title = title or ln
        elif any(k in lower for k in ("inc", "llc", "corp", "ltd", "labs", "capital", "pay", "bank")):
            company = company or ln

    blob = ocr_text.lower()
    tags: List[str] = []
    tag_map = {
        "payment": "payments",
        "fintech": "fintech",
        "legal": "legal",
        "law": "legal",
        "cloud": "cloud services",
        "retail": "retail",
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
