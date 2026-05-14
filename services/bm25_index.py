"""In-process BM25 index per user, rebuilt on document changes."""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import BM25_TOP_K
from models.orm import Chunk

logger = logging.getLogger(__name__)

# Global in-process store: user_id → BM25Index
_indexes: dict[UUID, "_BM25Index"] = {}


@dataclass
class _BM25Index:
    bm25: BM25Okapi
    chunk_ids: list[UUID]
    built_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BM25Result:
    chunk_id: UUID
    score: float
    rank: int


def _tokenize(text: str) -> list[str]:
    return re.split(r"[\s　 -/:-@[-`{-~]+", text.lower())


async def rebuild_bm25_index(db: AsyncSession, user_id: UUID) -> None:
    result = await db.execute(
        select(Chunk.id, Chunk.content).where(Chunk.user_id == user_id).order_by(Chunk.created_at)
    )
    rows = result.fetchall()

    if not rows:
        _indexes.pop(user_id, None)
        logger.info("bm25 index cleared (no chunks)", extra={"user_id": str(user_id)})
        return

    chunk_ids = [row.id for row in rows]
    corpus = [_tokenize(row.content) for row in rows]
    _indexes[user_id] = _BM25Index(bm25=BM25Okapi(corpus), chunk_ids=chunk_ids)
    logger.info("bm25 index built", extra={"user_id": str(user_id), "chunk_count": len(chunk_ids)})


def bm25_search(user_id: UUID, query: str, top_k: int = BM25_TOP_K) -> list[BM25Result]:
    index = _indexes.get(user_id)
    if index is None:
        return []

    scores = index.bm25.get_scores(_tokenize(query))
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    for rank, idx in enumerate(top_indices, start=1):
        if scores[idx] > 0:
            results.append(BM25Result(chunk_id=index.chunk_ids[idx], score=float(scores[idx]), rank=rank))

    return results
