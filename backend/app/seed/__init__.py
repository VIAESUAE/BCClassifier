from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import BusinessCard
from app.schemas import CardFields
from app.seed.data import SEED_CARDS
from app.services.embeddings import embed_texts
from app.services.extract import build_embedding_text
from app.services.geo import enrich_card_geo


def seed_if_empty(db: Session) -> int:
    """Insert missing seed cards and backfill country / geo_zone / timezone."""
    existing = list(db.scalars(select(BusinessCard)).all())
    by_email = {(c.email or "").lower(): c for c in existing if c.email}

    fields_list = [CardFields(**row) for row in SEED_CARDS]
    texts = [build_embedding_text(f) for f in fields_list]
    vectors = embed_texts(texts)

    inserted = 0
    for fields, text, vector in zip(fields_list, texts, vectors):
        key = (fields.email or "").lower()
        if key and key in by_email:
            card = by_email[key]
            country, timezone, geo_zone, city = enrich_card_geo(
                ocr_text=text,
                phone=fields.phone or card.phone,
                country=fields.country or card.country,
                region=fields.region or card.region,
                timezone=fields.timezone or card.timezone,
                geo_zone=fields.geo_zone or card.geo_zone,
            )
            card.country = fields.country or country
            card.timezone = fields.timezone or timezone
            card.geo_zone = fields.geo_zone or geo_zone
            card.region = fields.region or city or card.region
            card.phone = fields.phone or card.phone
            continue

        db.add(
            BusinessCard(
                full_name=fields.full_name,
                company=fields.company,
                title=fields.title,
                phone=fields.phone,
                email=fields.email,
                country=fields.country,
                timezone=fields.timezone,
                region=fields.region,
                geo_zone=fields.geo_zone,
                tags=fields.tags,
                notes=fields.notes,
                raw_ocr=text,
                image_path=None,
                embedding_text=text,
                embedding=vector,
                extra={"synthetic": True, "source": "seed"},
            )
        )
        inserted += 1

    # Backfill any non-seed rows missing geo
    for card in existing:
        if card.geo_zone and card.timezone and card.country:
            continue
        country, timezone, geo_zone, city = enrich_card_geo(
            ocr_text=card.raw_ocr or card.embedding_text or "",
            phone=card.phone,
            country=card.country,
            region=card.region,
            timezone=card.timezone,
            geo_zone=card.geo_zone,
        )
        card.country = card.country or country
        card.timezone = card.timezone or timezone
        card.geo_zone = card.geo_zone or geo_zone
        card.region = card.region or city

    db.commit()
    return inserted
