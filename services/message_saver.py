"""Service for saving messages after streaming completes."""

import traceback
from uuid import UUID

from models.orm import Conversation, Message
from core.database import get_session


async def save_chat_messages(
    user_id: UUID | None,
    conversation_id: UUID | None,
    user_message: str,
    assistant_content: str
) -> None:
    """
    Save user message and AI assistant response to database.

    If no conversation_id is provided but user_id is, creates a new conversation.
    """
    async with get_session() as session:
        try:
            conv_id = conversation_id

            # Create conversation if needed
            if not conv_id and user_id:
                conv = Conversation(user_id=user_id, title="New Chat")
                session.add(conv)
                await session.commit()
                await session.refresh(conv)
                conv_id = conv.id
                print(f"[Save] Created new conversation: {conv_id}")

            # Save user message
            if conv_id and user_message:
                user_msg = Message(
                    conversation_id=conv_id,
                    role="user",
                    content=user_message,
                )
                session.add(user_msg)
                print(f"[Save] Added user message to conv {conv_id}")

            # Save AI response
            if conv_id and assistant_content:
                assistant_msg = Message(
                    conversation_id=conv_id,
                    role="assistant",
                    content=assistant_content,
                )
                session.add(assistant_msg)
                print(f"[Save] Added assistant message to conv {conv_id}")

            await session.commit()
            print("[Save] Committed successfully")
        except Exception as e:
            print(f"[Save] Error saving messages: {e}")
            traceback.print_exc()
