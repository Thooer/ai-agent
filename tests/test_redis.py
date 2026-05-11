"""
Redis integration tests.
Run: python tests/test_redis.py
Requires Redis running at localhost:6379.
"""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.embedding_cache import get_cached_embedding, set_cached_embedding, set_cached_embeddings_batch
from services.rate_limiter import is_rate_limited, get_request_count
from services.task_state import create_task, update_task_progress, complete_task, fail_task, get_task
from core.redis_client import get_redis, close_redis

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"


def check(label: str, condition: bool):
    print(f"  [{PASS if condition else FAIL}] {label}")
    if not condition:
        raise AssertionError(label)


# ---------------------------------------------------------------------------
# Embedding cache
# ---------------------------------------------------------------------------

async def test_embedding_cache():
    print("\n[Embedding Cache]")

    text = "test sentence for embedding cache"
    vector = [0.1, 0.2, 0.3, 0.4, 0.5]

    # clean up keys from previous runs
    import hashlib
    from core.config import REDIS_PROJECT_PREFIX
    redis = await get_redis()
    key = f"{REDIS_PROJECT_PREFIX}:embed:{hashlib.sha256(text.encode()).hexdigest()}"
    await redis.delete(key)
    batch_keys = [
        f"{REDIS_PROJECT_PREFIX}:embed:{hashlib.sha256(f'batch text {i}'.encode()).hexdigest()}"
        for i in range(5)
    ]
    if batch_keys:
        await redis.delete(*batch_keys)

    # cache miss
    result = await get_cached_embedding(text)
    check("cache miss returns None", result is None)

    # cache set + hit
    await set_cached_embedding(text, vector)
    result = await get_cached_embedding(text)
    check("cache hit returns correct vector", result == vector)

    # different text is still a miss
    result2 = await get_cached_embedding("completely different text")
    check("different text is cache miss", result2 is None)

    # batch write
    pairs = [(f"batch text {i}", [float(i)] * 5) for i in range(5)]
    await set_cached_embeddings_batch(pairs)
    for text_b, vec_b in pairs:
        r = await get_cached_embedding(text_b)
        check(f"batch cache hit: '{text_b}'", r == vec_b)

    # TTL is set
    ttl = await redis.ttl(key)
    check("TTL is set (> 0)", ttl > 0)


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

async def test_rate_limiter():
    print("\n[Rate Limiter]")

    # use a unique user id to avoid interference from previous runs
    user_id = f"test-user-{int(time.time())}"

    # clean slate
    redis = await get_redis()
    from core.config import REDIS_PROJECT_PREFIX
    await redis.delete(f"{REDIS_PROJECT_PREFIX}:ratelimit:{user_id}")

    # first request should not be limited
    limited = await is_rate_limited(user_id)
    check("first request is not rate limited", not limited)

    count = await get_request_count(user_id)
    check("request count is 1 after first call", count == 1)

    # simulate hitting the limit (MAX_REQUESTS = 50)
    from services.rate_limiter import MAX_REQUESTS
    # already made 1 request above; make MAX_REQUESTS - 1 more to reach the limit
    for _ in range(MAX_REQUESTS - 1):
        await is_rate_limited(user_id)

    limited = await is_rate_limited(user_id)
    check(f"request is blocked after {MAX_REQUESTS} requests", limited)

    # sliding window: verify old entries are pruned on next check
    # replace all entries with timestamps 2 minutes ago
    key = f"{REDIS_PROJECT_PREFIX}:ratelimit:{user_id}"
    await redis.delete(key)
    old_ts = time.time() - 120
    for i in range(MAX_REQUESTS):
        await redis.zadd(key, {f"old-{i}": old_ts})

    # now the window should be clear — next request should not be limited
    limited_after_expiry = await is_rate_limited(user_id)
    check("not limited after sliding window clears old entries", not limited_after_expiry)


# ---------------------------------------------------------------------------
# Task state
# ---------------------------------------------------------------------------

async def test_task_state():
    print("\n[Task State]")

    task_id = await create_task()
    check("task created with non-empty id", bool(task_id))

    task = await get_task(task_id)
    check("initial status is pending", task["status"] == "pending")
    check("initial progress is 0", task["progress"] == "0")

    await update_task_progress(task_id, 50)
    task = await get_task(task_id)
    check("status is processing after update", task["status"] == "processing")
    check("progress updated to 50", task["progress"] == "50")

    await complete_task(task_id)
    task = await get_task(task_id)
    check("status is done after complete", task["status"] == "done")
    check("progress is 100 after complete", task["progress"] == "100")

    # fail path
    fail_id = await create_task()
    await fail_task(fail_id, "something went wrong")
    task = await get_task(fail_id)
    check("status is failed", task["status"] == "failed")
    check("error message stored", task["error"] == "something went wrong")

    # non-existent task
    result = await get_task("non-existent-id")
    check("non-existent task returns None", result is None)

    # TTL is set
    redis = await get_redis()
    from core.config import REDIS_PROJECT_PREFIX
    ttl = await redis.ttl(f"{REDIS_PROJECT_PREFIX}:task:{task_id}")
    check("TTL is set on task key", ttl > 0)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

async def main():
    print("=" * 50)
    print("Redis Integration Tests")
    print("=" * 50)

    try:
        redis = await get_redis()
        await redis.ping()
        print("Redis connection: OK")
    except Exception as e:
        print(f"Redis connection FAILED: {e}")
        sys.exit(1)

    failed = 0
    for test_fn in [test_embedding_cache, test_rate_limiter, test_task_state]:
        try:
            await test_fn()
        except AssertionError as e:
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {test_fn.__name__}: {e}")
            failed += 1

    await close_redis()

    print("\n" + "=" * 50)
    if failed == 0:
        print("All tests passed.")
    else:
        print(f"{failed} test(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
