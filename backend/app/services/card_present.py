from __future__ import annotations

from datetime import datetime
from typing import Optional

from zoneinfo import ZoneInfo

from app.db import BusinessCard
from app.schemas import CardOut
from app.services.geo import city_label_localized, enrich_card_geo, utc_offset_label


def card_to_out(card: BusinessCard, lang: str = "en") -> CardOut:
    _, _, _, inferred_city = enrich_card_geo(
        phone=card.phone,
        country=card.country,
        region=card.region,
        timezone=card.timezone,
        geo_zone=card.geo_zone,
    )
    city_en = inferred_city
    if lang == "zh":
        city_shown = city_label_localized(city_en, "zh") if city_en else card.region
    else:
        city_shown = city_en or card.region

    local_time = _format_local_clock(card.timezone)
    local_label = None
    if city_shown and local_time:
        if lang == "zh":
            local_label = f"{city_shown} · 当地时间 {local_time}"
        else:
            local_label = f"{city_shown} · local {local_time}"

    return CardOut(
        id=card.id,
        full_name=card.full_name,
        company=card.company,
        title=card.title,
        phone=card.phone,
        email=card.email,
        country=card.country,
        timezone=card.timezone,
        region=card.region,
        geo_zone=card.geo_zone,
        tags=card.tags or [],
        notes=card.notes,
        image_path=card.image_path,
        raw_ocr=card.raw_ocr,
        created_at=card.created_at.isoformat() if card.created_at else None,
        timezone_display=utc_offset_label(card.timezone),
        city_label=city_shown,
        local_time=local_time,
        local_time_label=local_label,
    )


def _format_local_clock(tz_name: Optional[str]) -> Optional[str]:
    if not tz_name:
        return None
    try:
        now = datetime.now(ZoneInfo(tz_name))
        return now.strftime("%H:%M")
    except Exception:
        return None
