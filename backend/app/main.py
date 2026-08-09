from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.db import BusinessCard
from app.routers import cards, ingest, rag
from app.schemas import HealthResponse
from app.seed import seed_if_empty
from app.services.llm_runtime import has_llm, set_request_llm_overrides


class LlmOverrideMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        set_request_llm_overrides(
            api_key=request.headers.get("x-openai-api-key"),
            base_url=request.headers.get("x-openai-base-url"),
            model=request.headers.get("x-openai-model"),
        )
        return await call_next(request)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    db = SessionLocal()
    try:
        seeded = seed_if_empty(db)
        if seeded:
            print(f"Seeded {seeded} synthetic business cards")
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Business Card Knowledge Base",
        description="Document AI ingest + hybrid RAG over synthetic business cards. Demo data — synthetic only.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list + ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LlmOverrideMiddleware)
    app.include_router(ingest.router)
    app.include_router(cards.router)
    app.include_router(rag.router)

    @app.get("/health", response_model=HealthResponse)
    def health():
        db = SessionLocal()
        try:
            count = db.scalar(select(func.count()).select_from(BusinessCard)) or 0
        finally:
            db.close()
        return HealthResponse(
            status="ok",
            demo_mode=settings.demo_mode,
            data_classification=settings.data_classification,
            has_llm=has_llm() or settings.has_llm,
            card_count=count,
        )

    return app


app = create_app()
