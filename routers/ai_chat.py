"""AI chat routes with streaming and RAG context."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse

from core.database import get_db
from core.security import get_current_user
from models.orm import User
from schemas.dto import ChatRequest, SseDelta, SseDone, SseError, SseRetrievalDone, SseRetrievalStart, sse
from services.hybrid_search import hybrid_search
from services.llm import LLMError, stream_chat
from services.message_saver import save_chat_messages
from services.rag_chat import build_rag_context
from services.rate_limiter import is_rate_limited
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat")
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if await is_rate_limited(str(current_user.id)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 50 requests per minute.")

    user_message = request.messages[-1].content if request.messages else ""

    async def event_generator():
        collected = []
        final_status = "completed"
        final_error: str | None = None
        citations = []

        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        # RAG retrieval
        if request.use_rag and user_message:
            yield sse(SseRetrievalStart())
            try:
                chunks = await hybrid_search(db, current_user.id, user_message)
            except Exception as e:
                logger.warning("retrieval failed, falling back to plain chat", extra={"error": str(e)})
                chunks = []

            citations = [
                {"doc_name": c.doc_name, "chunk_index": c.chunk_index,
                 "start_char": c.start_char, "end_char": c.end_char}
                for c in chunks
            ]
            yield sse(SseRetrievalDone(chunk_count=len(chunks)))

            context = build_rag_context(chunks)
            if context:
                messages = [{"role": "system", "content": context}] + messages

        try:
            async for content in stream_chat(messages):
                collected.append(content)
                yield sse(SseDelta(content=content))
            yield sse(SseDone(citations=citations))
        except LLMError as e:
            final_status = "failed"
            final_error = str(e)
            yield sse(SseError(message="模型服务暂时不可用，请稍后重试"))

        background_tasks.add_task(
            save_chat_messages,
            user_id=current_user.id,
            conversation_id=request.conversation_id,
            user_message=user_message,
            assistant_content="".join(collected),
            status=final_status,
            error_message=final_error,
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
