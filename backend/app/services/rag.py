from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import BusinessCard
from app.schemas import CardOut, RagHit, RagQueryResponse
from app.services.card_present import card_to_out
from app.services.embeddings import embed_query
from app.services.llm_runtime import effective_api_key, effective_base_url, effective_model, has_llm

WEST_COAST_HINTS = ("west coast", "bay area", "san francisco", "seattle", "los angeles", "california", "pst", "pdt")
EAST_COAST_HINTS = ("east coast", "new york", "nyc", "boston", "est", "edt")
GEO_ZONE_HINTS = {
    "APAC": ("apac", "asia pacific", "asia-pacific", "亚太", "東南亞", "东南亚", "singapore", "japan", "korea"),
    "NA": ("north america", "北美", "usa", "united states", "canada"),
    "LATAM": ("latam", "latin america", "拉美", "南美", "brazil", "mexico"),
    "EU": (" europe", "eu ", "欧盟", "欧洲", "london", "paris", "berlin"),
    "MEA": ("mea", "middle east", "africa", "中东", "非洲", "dubai", "uae"),
}
TAG_HINTS = {
    "payments": ("payment", "payments", "paytech", "checkout", "acquiring"),
    "fund bridging": ("fund bridg", "capital bridge", "bridge financing", "资金搭桥", "搭桥"),
    "fintech": ("fintech", "financial technology"),
    "venture capital": ("venture", "vc ", "investor"),
    "banking": ("bank", "banking"),
    "crypto": ("crypto", "web3", "blockchain"),
    "cloud services": ("cloud", "云服务", "aws", "azure", "saas infra"),
    "hardware": ("hardware", "硬件", "semiconductor", "server"),
    "legal": ("legal", "law", "counsel", "法律"),
    "retail": ("retail", "零售", "merchant store"),
    "logistics": ("logistics", "物流", "shipping", "parcel"),
}


def parse_query_filters(query: str) -> Dict[str, Any]:
    q = query.lower()
    filters: Dict[str, Any] = {
        "regions": [],
        "timezones": [],
        "tags": [],
        "geo_zones": [],
        "raw_query": query,
    }

    if any(h in q for h in WEST_COAST_HINTS) or "西海岸" in query:
        filters["regions"].append("US West Coast")
        filters["timezones"].extend(["America/Los_Angeles", "PST", "PDT", "PT"])
        if "NA" not in filters["geo_zones"]:
            filters["geo_zones"].append("NA")
    if any(h in q for h in EAST_COAST_HINTS) or "东海岸" in query:
        filters["regions"].append("US East Coast")
        filters["timezones"].extend(["America/New_York", "EST", "EDT", "ET"])
        if "NA" not in filters["geo_zones"]:
            filters["geo_zones"].append("NA")

    for zone, hints in GEO_ZONE_HINTS.items():
        if any(h in q for h in hints) or zone.lower() in q:
            filters["geo_zones"].append(zone)

    for tag, hints in TAG_HINTS.items():
        if any(h in q for h in hints):
            filters["tags"].append(tag)
    if "支付" in query and "payments" not in filters["tags"]:
        filters["tags"].append("payments")

    return filters


def hybrid_search(db: Session, query: str, top_k: int = 5) -> RagQueryResponse:
    settings = get_settings()
    filters = parse_query_filters(query)
    query_vec = embed_query(query)

    # Structural pre-filter in Python (works for Postgres ARRAY and SQLite JSON tags)
    all_cards = list(db.scalars(select(BusinessCard)).all())
    candidates: List[BusinessCard] = list(all_cards)

    if filters["geo_zones"]:
        zoned = [c for c in candidates if (c.geo_zone or "").upper() in filters["geo_zones"]]
        if zoned:
            candidates = zoned

    if filters["regions"] or filters["timezones"]:
        geo = []
        for card in candidates:
            region_ok = not filters["regions"] or bool(
                card.region and any(r.lower() in card.region.lower() for r in filters["regions"])
            )
            tz_ok = not filters["timezones"] or bool(
                card.timezone
                and any(tz.lower() in (card.timezone or "").lower() for tz in filters["timezones"])
            )
            if region_ok or tz_ok:
                geo.append(card)
        if geo:
            candidates = geo

    if filters["tags"]:
        tagged = [c for c in candidates if c.tags and any(t in (c.tags or []) for t in filters["tags"])]
        if tagged:
            candidates = tagged

    if not candidates:
        candidates = all_cards

    scored: List[Tuple[BusinessCard, float, str]] = []
    for card in candidates:
        score = _cosine(query_vec, card.embedding) if card.embedding is not None else 0.0
        reason_parts = []
        if card.geo_zone and filters["geo_zones"] and card.geo_zone.upper() in filters["geo_zones"]:
            score += 0.14
            reason_parts.append(f"geo_zone={card.geo_zone}")
        if card.region and filters["regions"] and any(r.lower() in (card.region or "").lower() for r in filters["regions"]):
            score += 0.12
            reason_parts.append(f"region={card.region}")
        if card.timezone and filters["timezones"] and any(
            tz.lower() in (card.timezone or "").lower() for tz in filters["timezones"]
        ):
            score += 0.08
            reason_parts.append(f"timezone={card.timezone}")
        card_tags = card.tags or []
        matched_tags = [t for t in filters["tags"] if t in card_tags]
        if matched_tags:
            score += 0.15 * len(matched_tags)
            reason_parts.append("tags=" + ",".join(matched_tags))
        if not reason_parts:
            reason_parts.append("semantic similarity")
        scored.append((card, score, "; ".join(reason_parts)))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]
    hits = [
        RagHit(
            card=card_to_out(card),
            score=round(float(score), 4),
            match_reason=reason,
        )
        for card, score, reason in top
    ]

    answer = _generate_answer(query, hits)
    notice = None
    if settings.demo_mode:
        notice = "Demo data — synthetic only. Do not upload real business cards to public deployments."

    return RagQueryResponse(
        answer=answer,
        hits=hits,
        filters_applied={
            "regions": filters["regions"],
            "timezones": filters["timezones"],
            "tags": filters["tags"],
            "geo_zones": filters["geo_zones"],
        },
        demo_notice=notice,
    )


def _cosine(a: List[float], b) -> float:
    if b is None:
        return 0.0
    bv = list(b)
    if not a or not bv or len(a) != len(bv):
        return 0.0
    dot = sum(x * y for x, y in zip(a, bv))
    na = math_sqrt(sum(x * x for x in a))
    nb = math_sqrt(sum(y * y for y in bv))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def math_sqrt(x: float) -> float:
    return x**0.5


def _to_card_out(card: BusinessCard) -> CardOut:
    """Back-compat alias used by routers."""
    return card_to_out(card)


def _generate_answer(query: str, hits: List[RagHit]) -> str:
    settings = get_settings()
    if not hits:
        return "No matching contacts found. Try broadening region or industry terms."

    if has_llm():
        try:
            return _llm_answer(query, hits)
        except Exception:
            pass
    return _template_answer(query, hits)


def _template_answer(query: str, hits: List[RagHit]) -> str:
    lines = [f"For “{query}”, here are the best-matching contacts from the card knowledge base:"]
    for i, hit in enumerate(hits, 1):
        c = hit.card
        tags = ", ".join(c.tags) if c.tags else "—"
        lines.append(
            f"{i}. {c.full_name} — {c.title or 'N/A'} at {c.company or 'N/A'} "
            f"({c.region or 'region n/a'}, {c.timezone or 'tz n/a'}; tags: {tags}). "
            f"Match: {hit.match_reason}."
        )
    lines.append("All answers are grounded in stored card fields (synthetic demo data unless privately deployed).")
    return "\n".join(lines)


def _llm_answer(query: str, hits: List[RagHit]) -> str:
    payload_cards = [
        {
            "name": h.card.full_name,
            "company": h.card.company,
            "title": h.card.title,
            "country": h.card.country,
            "region": h.card.region,
            "geo_zone": h.card.geo_zone,
            "timezone": h.card.timezone,
            "tags": h.card.tags,
            "email": h.card.email,
            "phone": h.card.phone,
            "match_reason": h.match_reason,
            "score": h.score,
        }
        for h in hits
    ]
    system = (
        "You are a business-card knowledge assistant. Answer ONLY using the provided contacts. "
        "Cite names and companies. If nothing fits, say so. Be concise."
    )
    user = f"Question: {query}\n\nContacts JSON:\n{json.dumps(payload_cards, ensure_ascii=False)}"
    headers = {
        "Authorization": f"Bearer {effective_api_key()}",
        "Content-Type": "application/json",
    }
    body = {
        "model": effective_model(),
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    with httpx.Client(base_url=effective_base_url(), timeout=60.0) as client:
        resp = client.post("/chat/completions", headers=headers, json=body)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


def find_dedupe_hits(db: Session, email: Optional[str], phone: Optional[str]) -> List[CardOut]:
    conditions = []
    if email:
        conditions.append(BusinessCard.email == email)
    if phone:
        normalized = re.sub(r"[^\d+]", "", phone)
        if len(normalized) >= 7:
            conditions.append(BusinessCard.phone.ilike(f"%{normalized[-7:]}%"))
    if not conditions:
        return []
    rows = list(db.scalars(select(BusinessCard).where(or_(*conditions)).limit(5)).all())
    return [_to_card_out(r) for r in rows]
