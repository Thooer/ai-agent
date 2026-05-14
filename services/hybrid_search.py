"""Hybrid search: vector + BM25 + RRF fusion."""

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import VECTOR_TOP_K, BM25_TOP_K, FINAL_TOP_K, RRF_K, RAG_RELEVANCE_THRESHOLD
from models.orm import Chunk, Document
from services.bm25_index import bm25_search
from services.embedding_service import embed
from services.rrf import rrf_merge
from services.vector_retrieval import vector_search

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: UUID
    doc_id: UUID
    doc_name: str
    chunk_index: int
    content: str
    start_char: int
    end_char: int
    rrf_score: float
    vector_rank: int | None
    bm25_rank: int | None


async def hybrid_search(
    db: AsyncSession,
    user_id: UUID,
    query: str,
    vector_top_k: int = VECTOR_TOP_K,
    bm25_top_k: int = BM25_TOP_K,
    final_top_k: int = FINAL_TOP_K,
    rrf_k: int = RRF_K,
) -> list[RetrievedChunk]:
    query_embedding = await embed(query)

    vector_results = await vector_search(db, user_id, query_embedding, top_k=vector_top_k)
    bm25_results = bm25_search(user_id, query, top_k=bm25_top_k)

    logger.info("retrieval", extra={
        "user_id": str(user_id),
        "vector_hits": len(vector_results),
        "bm25_hits": len(bm25_results),
    })

    merged = rrf_merge(
        vector_ids=[r.chunk_id for r in vector_results],
        bm25_ids=[r.chunk_id for r in bm25_results],
        k=rrf_k,
        top_k=final_top_k,
    )

    if not merged:
        return []

    # Check relevance threshold using best vector score
    best_vector_score = vector_results[0].score if vector_results else 0.0
    if best_vector_score < RAG_RELEVANCE_THRESHOLD:
        logger.info("below relevance threshold", extra={"best_score": best_vector_score})
        return []

    # Fetch full chunk content for merged results
    chunk_ids = [r.chunk_id for r in merged]
    rows = await db.execute(
        select(Chunk, Document.name.label("doc_name"))
        .join(Document, Chunk.doc_id == Document.id)
        .where(Chunk.id.in_(chunk_ids))
    )
    chunk_map = {row.Chunk.id: (row.Chunk, row.doc_name) for row in rows}

    retrieved: list[RetrievedChunk] = []
    for rrf_result in merged:
        entry = chunk_map.get(rrf_result.chunk_id)
        if entry is None:
            continue
        chunk, doc_name = entry
        retrieved.append(RetrievedChunk(
            chunk_id=chunk.id,
            doc_id=chunk.doc_id,
            doc_name=doc_name,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            rrf_score=rrf_result.rrf_score,
            vector_rank=rrf_result.vector_rank,
            bm25_rank=rrf_result.bm25_rank,
        ))

    return retrieved
