"""Task state management for long-running document ingestion jobs."""

import uuid

from core.redis_client import get_redis
from core.config import REDIS_PROJECT_PREFIX

TTL = 3600  # 1 hour

STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_DONE = "done"
STATUS_FAILED = "failed"


def _key(task_id: str) -> str:
    return f"{REDIS_PROJECT_PREFIX}:task:{task_id}"


async def create_task() -> str:
    task_id = str(uuid.uuid4())
    redis = await get_redis()
    await redis.hset(_key(task_id), mapping={
        "status": STATUS_PENDING,
        "progress": 0,
        "error": "",
    })
    await redis.expire(_key(task_id), TTL)
    return task_id


async def update_task_progress(task_id: str, progress: int) -> None:
    redis = await get_redis()
    await redis.hset(_key(task_id), mapping={
        "status": STATUS_PROCESSING,
        "progress": progress,
    })


async def complete_task(task_id: str) -> None:
    redis = await get_redis()
    await redis.hset(_key(task_id), mapping={
        "status": STATUS_DONE,
        "progress": 100,
    })


async def fail_task(task_id: str, error: str) -> None:
    redis = await get_redis()
    await redis.hset(_key(task_id), mapping={
        "status": STATUS_FAILED,
        "error": error,
    })


async def get_task(task_id: str) -> dict | None:
    redis = await get_redis()
    raw = await redis.hgetall(_key(task_id))
    if not raw:
        return None
    return {k.decode(): v.decode() for k, v in raw.items()}
