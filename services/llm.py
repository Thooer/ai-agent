"""LLM service for streaming chat."""

import asyncio
import json
from typing import AsyncGenerator

import httpx
from fastapi import HTTPException

from core.config import BIGMODEL_API_KEY, BIGMODEL_BASE_URL

_TIMEOUT = httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)
_MAX_RETRIES = 2
_RETRY_DELAY = 1.0


class LLMError(Exception):
    pass


async def stream_chat(messages: list[dict]) -> AsyncGenerator[str, None]:
    """Stream chat completion; retries on transient errors, yields raw content strings."""
    headers = {
        "Authorization": f"Bearer {BIGMODEL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "glm-5.1",
        "messages": messages,
        "stream": True,
    }

    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        if attempt > 0:
            await asyncio.sleep(_RETRY_DELAY)

        try:
            async with httpx.AsyncClient(trust_env=False, timeout=_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{BIGMODEL_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code >= 500:
                        # 5xx is transient, worth retrying
                        error_body = await response.aread()
                        last_error = LLMError(f"HTTP {response.status_code}: {error_body.decode()}")
                        continue
                    if response.status_code >= 400:
                        # 4xx is a caller error, no point retrying
                        error_body = await response.aread()
                        raise LLMError(f"HTTP {response.status_code}: {error_body.decode()}")

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data == "[DONE]":
                            return
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
                    return  # clean stream end

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            last_error = LLMError(f"Network error: {e}")
            continue

    raise LLMError(str(last_error))
