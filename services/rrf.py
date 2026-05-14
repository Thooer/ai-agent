"""Reciprocal Rank Fusion — pure function, no I/O."""

from dataclasses import dataclass
from uuid import UUID

from core.config import RRF_K, FINAL_TOP_K


@dataclass
class RankedResult:
    chunk_id: UUID
    rrf_score: float
    vector_rank: int | None
    bm25_rank: int | None


def rrf_merge(
    vector_ids: list[UUID],
    bm25_ids: list[UUID],
    k: int = RRF_K,
    top_k: int = FINAL_TOP_K,
) -> list[RankedResult]:
    scores: dict[UUID, float] = {}
    v_rank: dict[UUID, int] = {}
    b_rank: dict[UUID, int] = {}

    for rank, cid in enumerate(vector_ids, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
        v_rank[cid] = rank

    for rank, cid in enumerate(bm25_ids, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
        b_rank[cid] = rank

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [
        RankedResult(
            chunk_id=cid,
            rrf_score=score,
            vector_rank=v_rank.get(cid),
            bm25_rank=b_rank.get(cid),
        )
        for cid, score in ranked
    ]
