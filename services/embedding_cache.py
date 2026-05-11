"""Embedding cache: store and retrieve vectors by text hash."""

import hashlib
import msgpack

from core.redis_client import get_redis
from core.config import REDIS_PROJECT_PREFIX

TTL = 7 * 24 * 3600  # 7 days


def _key(text: str) -> str:
    digest = hashlib.sha256(text.encode()).hexdigest()
    return f"{REDIS_PROJECT_PREFIX}:embed:{digest}"


async def get_cached_embedding(text: str) -> list[float] | None:
    redis = await get_redis()
    raw = await redis.get(_key(text))
    if raw is None:
        return None
    return msgpack.unpackb(raw)


async def set_cached_embedding(text: str, vector: list[float]) -> None:
    redis = await get_redis()
    packed = msgpack.packb(vector)
    await redis.set(_key(text), packed, ex=TTL)


async def set_cached_embeddings_batch(pairs: list[tuple[str, list[float]]]) -> None:
    """Pipeline batch write for multiple text-vector pairs."""
    redis = await get_redis()
    async with redis.pipeline(transaction=False) as pipe:
        for text, vector in pairs:
            packed = msgpack.packb(vector)
            pipe.set(_key(text), packed, ex=TTL)
        await pipe.execute()
