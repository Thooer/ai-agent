"""Rate limiter: sliding window via ZSET."""

import time

from core.redis_client import get_redis
from core.config import REDIS_PROJECT_PREFIX

WINDOW_SECONDS = 60
MAX_REQUESTS = int(50)  # per user per minute


def _key(user_id: str) -> str:
    return f"{REDIS_PROJECT_PREFIX}:ratelimit:{user_id}"


async def is_rate_limited(user_id: str) -> bool:
    """Return True if user has exceeded the rate limit."""
    redis = await get_redis()
    key = _key(user_id)
    now = time.time()
    window_start = now - WINDOW_SECONDS

    async with redis.pipeline(transaction=True) as pipe:
        pipe.zremrangebyscore(key, "-inf", window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, WINDOW_SECONDS * 2)
        results = await pipe.execute()

    count_before_add = results[1]
    return count_before_add >= MAX_REQUESTS


async def get_request_count(user_id: str) -> int:
    """Return current request count in the sliding window."""
    redis = await get_redis()
    key = _key(user_id)
    now = time.time()
    window_start = now - WINDOW_SECONDS
    await redis.zremrangebyscore(key, "-inf", window_start)
    return await redis.zcard(key)
