"""Embedding service: zhipu embedding-3, batched, cached."""

import asyncio
import logging

import httpx

from core.config import BIGMODEL_API_KEY, BIGMODEL_BASE_URL, EMBEDDING_MODEL, EMBEDDING_DIM, EMBEDDING_BATCH_SIZE
from services.embedding_cache import get_cached_embedding, set_cached_embeddings_batch

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
_MAX_RETRIES = 3
_RETRY_DELAY = 1.0


class EmbeddingError(Exception):
    pass


async def _call_api(texts: list[str]) -> list[list[float]]:
    headers = {"Authorization": f"Bearer {BIGMODEL_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": EMBEDDING_MODEL, "input": texts, "dimensions": EMBEDDING_DIM}

    for attempt in range(_MAX_RETRIES):
        try:
            async with httpx.AsyncClient(trust_env=False, timeout=_TIMEOUT) as client:
                resp = await client.post(f"{BIGMODEL_BASE_URL}/embeddings", headers=headers, json=payload)
                if resp.status_code == 429:
                    await asyncio.sleep(_RETRY_DELAY * (attempt + 1))
                    continue
                if resp.status_code != 200:
                    raise EmbeddingError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
                vectors = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
                if any(len(v) != EMBEDDING_DIM for v in vectors):
                    raise EmbeddingError(f"Expected dim {EMBEDDING_DIM}, got {len(vectors[0])}")
                return vectors
        except httpx.TimeoutException as e:
            if attempt == _MAX_RETRIES - 1:
                raise EmbeddingError(f"Timeout after {_MAX_RETRIES} retries: {e}")
            await asyncio.sleep(_RETRY_DELAY)

    raise EmbeddingError("Max retries exceeded")


async def embed(text: str) -> list[float]:
    cached = await get_cached_embedding(text)
    if cached is not None:
        return cached
    vectors = await _call_api([text])
    await set_cached_embeddings_batch([(text, vectors[0])])
    return vectors[0]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    # Check cache first
    results: list[list[float] | None] = [None] * len(texts)
    miss_indices: list[int] = []

    for i, text in enumerate(texts):
        cached = await get_cached_embedding(text)
        if cached is not None:
            results[i] = cached
        else:
            miss_indices.append(i)

    if not miss_indices:
        return results  # type: ignore[return-value]

    # Batch API calls for cache misses
    miss_texts = [texts[i] for i in miss_indices]
    fetched: list[list[float]] = []
    for start in range(0, len(miss_texts), EMBEDDING_BATCH_SIZE):
        batch = miss_texts[start: start + EMBEDDING_BATCH_SIZE]
        batch_vectors = await _call_api(batch)
        fetched.extend(batch_vectors)
        logger.info("embedded batch", extra={"batch_size": len(batch), "total_fetched": len(fetched)})

    # Write back to cache
    await set_cached_embeddings_batch(list(zip(miss_texts, fetched)))

    for idx, vector in zip(miss_indices, fetched):
        results[idx] = vector

    return results  # type: ignore[return-value]
