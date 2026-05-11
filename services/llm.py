"""LLM service for streaming chat."""

import json
from typing import AsyncGenerator

import httpx
from fastapi import HTTPException

from core.config import BIGMODEL_API_KEY, BIGMODEL_BASE_URL


async def stream_chat(messages: list[dict]) -> AsyncGenerator[str, None]:
    """Stream chat completion from BigModel API."""
    headers = {
        "Authorization": f"Bearer {BIGMODEL_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "glm-5.1",
        "messages": messages,
        "stream": True,
    }

    async with httpx.AsyncClient(trust_env=False) as client:
        async with client.stream(
            "POST",
            f"{BIGMODEL_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60.0,
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                raise HTTPException(status_code=response.status_code, detail=error_text.decode())

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield f"data: {json.dumps({'content': content})}\n\n"
                    except json.JSONDecodeError:
                        continue
