"""AI chat routes with streaming."""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from schemas.dto import ChatRequest, SseDelta, SseDone, SseError, sse
from services.llm import stream_chat, LLMError
from services.message_saver import save_chat_messages
from services.rate_limiter import is_rate_limited

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    if await is_rate_limited(str(request.user_id)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 50 requests per minute.")

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    user_id = request.user_id
    conversation_id = request.conversation_id
    user_message = request.messages[-1].content if request.messages else ""

    async def event_generator():
        collected = []
        final_status = "completed"
        final_error: str | None = None

        try:
            async for content in stream_chat(messages):
                collected.append(content)
                yield sse(SseDelta(content=content))
            yield sse(SseDone())
        except LLMError as e:
            final_status = "failed"
            final_error = str(e)
            yield sse(SseError(message="模型服务暂时不可用，请稍后重试"))

        background_tasks.add_task(
            save_chat_messages,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_content="".join(collected),
            status=final_status,
            error_message=final_error,
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
