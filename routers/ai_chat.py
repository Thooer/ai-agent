"""AI chat routes with streaming."""

import json
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from schemas.dto import ChatRequest, ChatMessage
from services.llm import stream_chat
from services.message_saver import save_chat_messages

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat")
async def chat(request: ChatRequest):
    """Stream chat completion and save messages."""

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    user_id = request.user_id
    conversation_id = request.conversation_id
    # Get the last user message to save
    user_message = request.messages[-1].content if request.messages else ""

    async def event_generator():
        full_response = []

        # Stream LLM response to client
        async for chunk in stream_chat(messages):
            yield chunk
            try:
                data = json.loads(chunk[6:])
                full_response.append(data.get("content", ""))
            except:
                pass

        yield "data: [DONE]\n\n"

        # Save messages after streaming completes
        assistant_content = "".join(full_response)
        print(
            f"[Save] user_id={user_id}, conv_id={conversation_id}, "
            f"user_msg_len={len(user_message)}, ai_msg_len={len(assistant_content)}"
        )

        await save_chat_messages(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_content=assistant_content,
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
