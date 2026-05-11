"""AI chat routes with streaming."""

import asyncio
import json

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from schemas.dto import ChatRequest
from services.llm import stream_chat
from services.message_saver import save_chat_messages
from services.rate_limiter import is_rate_limited

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Stream chat completion and save messages."""
    if await is_rate_limited(str(request.user_id)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 50 requests per minute.")

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    user_id = request.user_id
    conversation_id = request.conversation_id
    user_message = request.messages[-1].content if request.messages else ""

    async def event_generator():
        full_response = []

        async for chunk in stream_chat(messages):
            yield chunk
            try:
                data = json.loads(chunk[6:])
                full_response.append(data.get("content", ""))
            except:
                pass

        yield "data: [DONE]\n\n"

        # 流结束后在后台保存，不阻塞连接关闭
        assistant_content = "".join(full_response)
        background_tasks.add_task(
            save_chat_messages,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_content=assistant_content,
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
