"""Service for saving messages after streaming completes."""

import logging
from uuid import UUID

from models.orm import Conversation, Message
from core.database import get_session

logger = logging.getLogger(__name__)


async def save_chat_messages(
    user_id: UUID | None,
    conversation_id: UUID | None,
    user_message: str,
    assistant_content: str,
    status: str = "completed",
    error_message: str | None = None,
) -> None:
    async with get_session() as session:
        try:
            conv_id = conversation_id

            if not conv_id and user_id:
                conv = Conversation(user_id=user_id, title="New Chat")
                session.add(conv)
                await session.commit()
                await session.refresh(conv)
                conv_id = conv.id

            if conv_id and user_message:
                session.add(Message(
                    conversation_id=conv_id,
                    role="user",
                    content=user_message,
                ))

            # Always save assistant message if there's content or it was a failure
            if conv_id and (assistant_content or status == "failed"):
                session.add(Message(
                    conversation_id=conv_id,
                    role="assistant",
                    content=assistant_content,
                    status=status,
                    error_message=error_message,
                ))

            await session.commit()
        except Exception:
            logger.exception("Failed to save chat messages")
