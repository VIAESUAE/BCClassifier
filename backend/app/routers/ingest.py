from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.db import BusinessCard
from app.schemas import (
    CardOut,
    IngestConfirmRequest,
    IngestPreviewResponse,
)
from app.services.embeddings import embed_texts
from app.services.extract import build_embedding_text, extract_fields
from app.services.geo import enrich_card_geo
from app.services.ocr import ocr_or_empty
from app.services.preprocess import preprocess_card_image, save_upload
from app.services.preview_store import PreviewSession, get_preview, pop_preview, put_preview
from app.services.rag import _to_card_out, find_dedupe_hits

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/preview", response_model=IngestPreviewResponse)
async def ingest_preview(file: UploadFile = File(...), db: Session = Depends(get_db)):
    suffix = Path(file.filename or "card.jpg").suffix or ".jpg"
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty upload")

    original = save_upload(raw, suffix=suffix)
    processed, _meta = preprocess_card_image(original)
    ocr_text, ocr_err = ocr_or_empty(processed)
    warnings = []
    if ocr_err:
        warnings.append(ocr_err)
    if not ocr_text.strip():
        warnings.append("OCR returned little/no text — edit fields manually or retake the photo.")

    extracted, extract_warnings = extract_fields(ocr_text)
    warnings.extend(extract_warnings)

    preview_id = uuid.uuid4().hex
    put_preview(
        PreviewSession(
            preview_id=preview_id,
            original_path=original,
            processed_path=processed,
            raw_ocr=ocr_text,
            extracted=extracted,
            warnings=warnings,
        )
    )

    dedupe = find_dedupe_hits(db, extracted.email, extracted.phone)
    return IngestPreviewResponse(
        preview_id=preview_id,
        original_image_url=f"/ingest/files/{original.name}",
        processed_image_url=f"/ingest/files/{processed.name}",
        raw_ocr=ocr_text,
        extracted=extracted,
        warnings=warnings,
        dedupe_hits=dedupe,
    )


@router.post("/confirm", response_model=CardOut)
def ingest_confirm(body: IngestConfirmRequest, db: Session = Depends(get_db)):
    session = pop_preview(body.preview_id)
    if not session:
        raise HTTPException(status_code=404, detail="Preview expired or not found")

    fields = body.fields
    country, timezone, geo_zone, city = enrich_card_geo(
        ocr_text=session.raw_ocr,
        phone=fields.phone,
        country=fields.country,
        region=fields.region,
        timezone=fields.timezone,
        geo_zone=fields.geo_zone,
    )
    fields = fields.model_copy(
        update={
            "country": country,
            "timezone": timezone,
            "geo_zone": geo_zone,
            "region": fields.region or city,
        }
    )
    embedding_text = build_embedding_text(fields)
    vector = embed_texts([embedding_text])[0]

    # Soft dedupe warning already shown; still allow save
    card = BusinessCard(
        full_name=fields.full_name,
        company=fields.company,
        title=fields.title,
        phone=fields.phone,
        email=fields.email,
        country=fields.country,
        timezone=fields.timezone,
        region=fields.region,
        geo_zone=fields.geo_zone,
        tags=fields.tags or [],
        notes=fields.notes,
        raw_ocr=session.raw_ocr,
        image_path=str(session.processed_path.name),
        embedding_text=embedding_text,
        embedding=vector,
        extra={"original_image": session.original_path.name},
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return _to_card_out(card)


@router.get("/files/{filename}")
def get_ingest_file(filename: str):
    # Prevent path traversal
    safe = Path(filename).name
    from app.config import get_settings

    path = Path(get_settings().upload_dir) / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@router.get("/preview/{preview_id}", response_model=IngestPreviewResponse)
def get_preview_state(preview_id: str, db: Session = Depends(get_db)):
    session = get_preview(preview_id)
    if not session:
        raise HTTPException(status_code=404, detail="Preview not found")
    dedupe = find_dedupe_hits(db, session.extracted.email, session.extracted.phone)
    return IngestPreviewResponse(
        preview_id=session.preview_id,
        original_image_url=f"/ingest/files/{session.original_path.name}",
        processed_image_url=f"/ingest/files/{session.processed_path.name}",
        raw_ocr=session.raw_ocr,
        extracted=session.extracted,
        warnings=session.warnings,
        dedupe_hits=dedupe,
    )
