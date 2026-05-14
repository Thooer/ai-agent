"""RAG debug search endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from models.orm import User
from services.bm25_index import bm25_search
from services.embedding_service import embed
from services.hybrid_search import hybrid_search
from services.vector_retrieval import vector_search

router = APIRouter(prefix="/rag", tags=["rag"])


class SearchRequest(BaseModel):
    query: str


@router.post("/search")
async def search(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query_embedding = await embed(body.query)
    v_results = await vector_search(db, current_user.id, query_embedding)
    b_results = bm25_search(current_user.id, body.query)
    final = await hybrid_search(db, current_user.id, body.query)

    return {
        "query": body.query,
        "final_chunks": [
            {
                "doc_name": c.doc_name,
                "chunk_index": c.chunk_index,
                "rrf_score": round(c.rrf_score, 4),
                "vector_rank": c.vector_rank,
                "bm25_rank": c.bm25_rank,
                "content": c.content[:200],
            }
            for c in final
        ],
        "vector_results": [
            {"chunk_id": str(r.chunk_id), "score": round(r.score, 4), "rank": r.rank}
            for r in v_results
        ],
        "bm25_results": [
            {"chunk_id": str(r.chunk_id), "score": round(r.score, 4), "rank": r.rank}
            for r in b_results
        ],
    }
