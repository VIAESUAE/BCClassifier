from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.db import BusinessCard
from app.schemas import CardOut
from app.services.card_present import card_to_out
from app.services.markets import (
    GEO_ZONES,
    card_matches_other,
    card_matches_place,
    filter_tree_for_lang,
)

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/filters")
def card_filters(lang: Optional[str] = Query("zh")):
    """Cascading Directory filters: geo zone → country / NA market slice."""
    return {"zones": filter_tree_for_lang(lang or "zh")}


@router.get("", response_model=List[CardOut])
def list_cards(
    geo_zone: Optional[str] = Query(None, description="APAC | NA | LATAM | EU | MEA"),
    place: Optional[str] = Query(
        None,
        description="Country / NA slice / Other",
    ),
    lang: Optional[str] = Query("zh", description="zh | en for local-time labels"),
    db: Session = Depends(get_db),
):
    stmt = select(BusinessCard).order_by(BusinessCard.id.desc())
    rows = list(db.scalars(stmt).all())
    if geo_zone:
        zone = geo_zone.upper()
        if zone not in GEO_ZONES:
            raise HTTPException(status_code=400, detail=f"geo_zone must be one of {list(GEO_ZONES)}")
        rows = [r for r in rows if (r.geo_zone or "").upper() == zone]
    if place:
        if place == "Other":
            zone = (geo_zone or "").upper()
            rows = [
                r
                for r in rows
                if card_matches_other(r.country, r.region, r.timezone, zone or r.geo_zone)
            ]
        else:
            rows = [r for r in rows if card_matches_place(r.country, r.region, r.timezone, place)]
    ui_lang = "zh" if (lang or "zh").startswith("zh") else "en"
    return [card_to_out(r, lang=ui_lang) for r in rows]


@router.get("/{card_id}", response_model=CardOut)
def get_card(
    card_id: int,
    lang: Optional[str] = Query("zh"),
    db: Session = Depends(get_db),
):
    card = db.get(BusinessCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    ui_lang = "zh" if (lang or "zh").startswith("zh") else "en"
    return card_to_out(card, lang=ui_lang)


@router.delete("/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.get(BusinessCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    db.delete(card)
    db.commit()
    return {"ok": True}
