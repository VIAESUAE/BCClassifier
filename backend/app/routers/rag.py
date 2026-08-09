from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import RagQueryRequest, RagQueryResponse
from app.services.rag import hybrid_search

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=RagQueryResponse)
def rag_query(body: RagQueryRequest, db: Session = Depends(get_db)):
    return hybrid_search(db, body.query, top_k=body.top_k)
