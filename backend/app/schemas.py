from typing import List, Optional

from pydantic import BaseModel, Field


class CardFields(BaseModel):
    full_name: str = Field(..., description="Person full name")
    company: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = Field(None, description="Country inferred from address / phone")
    timezone: Optional[str] = Field(
        None, description="IANA timezone, e.g. America/New_York or Asia/Singapore"
    )
    region: Optional[str] = Field(None, description="City / local area, e.g. Bay Area, New York")
    geo_zone: Optional[str] = Field(
        None, description="Business region: APAC | NA | LATAM | EU | MEA"
    )
    tags: List[str] = Field(default_factory=list, description="Industry / focus tags")
    notes: Optional[str] = None


class CardOut(CardFields):
    id: int
    image_path: Optional[str] = None
    raw_ocr: Optional[str] = None
    created_at: Optional[str] = None
    timezone_display: Optional[str] = None
    city_label: Optional[str] = None
    local_time: Optional[str] = None
    local_time_label: Optional[str] = None

    model_config = {"from_attributes": True}


class IngestPreviewResponse(BaseModel):
    preview_id: str
    original_image_url: str
    processed_image_url: str
    raw_ocr: str
    extracted: CardFields
    warnings: List[str] = Field(default_factory=list)
    dedupe_hits: List[CardOut] = Field(default_factory=list)


class IngestConfirmRequest(BaseModel):
    preview_id: str
    fields: CardFields


class RagQueryRequest(BaseModel):
    query: str
    top_k: int = 5


class RagHit(BaseModel):
    card: CardOut
    score: float
    match_reason: str


class RagQueryResponse(BaseModel):
    answer: str
    hits: List[RagHit]
    filters_applied: dict
    demo_notice: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    demo_mode: bool
    data_classification: str
    has_llm: bool
    card_count: int
