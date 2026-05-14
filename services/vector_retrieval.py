"""pgvector cosine similarity search."""

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import VECTOR_TOP_K

logger = logging.getLogger(__name__)


@dataclass
class VectorResult:
    chunk_id: UUID
    doc_id: UUID
    doc_name: str
    chunk_index: int
    content: str
    start_char: int
    end_char: int
    score: float
    rank: int


async def vector_search(
    db: AsyncSession,
    user_id: UUID,
    query_embedding: list[float],
    top_k: int = VECTOR_TOP_K,
) -> list[VectorResult]:
    sql = text("""
        SELECT
            c.id,
            c.doc_id,
            d.name AS doc_name,
            c.chunk_index,
            c.content,
            c.start_char,
            c.end_char,
            1 - (c.embedding <=> CAST(:embedding AS vector)) AS score
        FROM chunks c
        JOIN documents d ON c.doc_id = d.id
        WHERE c.user_id = :user_id
          AND c.embedding IS NOT NULL
        ORDER BY c.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)

    result = await db.execute(sql, {
        "embedding": str(query_embedding),
        "user_id": str(user_id),
        "top_k": top_k,
    })
    rows = result.fetchall()

    return [
        VectorResult(
            chunk_id=row.id,
            doc_id=row.doc_id,
            doc_name=row.doc_name,
            chunk_index=row.chunk_index,
            content=row.content,
            start_char=row.start_char,
            end_char=row.end_char,
            score=float(row.score),
            rank=i + 1,
        )
        for i, row in enumerate(rows)
    ]
