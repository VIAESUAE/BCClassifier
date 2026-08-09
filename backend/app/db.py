from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
_IS_SQLITE = settings.database_url.startswith("sqlite")


def _vector_column():
    if _IS_SQLITE:
        return mapped_column(JSON, nullable=True)
    from pgvector.sqlalchemy import Vector

    return mapped_column(Vector(settings.embedding_dim), nullable=True)


def _tags_column():
    if _IS_SQLITE:
        return mapped_column(JSON, default=list)
    from sqlalchemy.dialects.postgresql import ARRAY

    return mapped_column(ARRAY(String), default=list)


def _extra_column():
    if _IS_SQLITE:
        return mapped_column(JSON, default=dict)
    from sqlalchemy.dialects.postgresql import JSONB

    return mapped_column(JSONB, default=dict)


class BusinessCard(Base):
    __tablename__ = "business_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    country: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    region: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    geo_zone: Mapped[Optional[str]] = mapped_column(String(16), index=True)
    tags: Mapped[Optional[List[str]]] = _tags_column()
    notes: Mapped[Optional[str]] = mapped_column(Text)
    raw_ocr: Mapped[Optional[str]] = mapped_column(Text)
    image_path: Mapped[Optional[str]] = mapped_column(String(512))
    embedding_text: Mapped[Optional[str]] = mapped_column(Text)
    embedding = _vector_column()
    extra: Mapped[Optional[dict]] = _extra_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
