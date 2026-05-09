"""Message routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.orm import Message
from schemas.dto import MessageCreate, MessageResponse

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageResponse)
async def create_message(
    message: MessageCreate, session: AsyncSession = Depends(get_db)
):
    db_message = Message(
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
    )
    session.add(db_message)
    await session.commit()
    await session.refresh(db_message)
    return db_message


@router.get("/conversation/{conversation_id}", response_model=list[MessageResponse])
async def list_messages(conversation_id: UUID, session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return result.scalars().all()


@router.delete("/{message_id}")
async def delete_message(message_id: UUID, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    await session.delete(message)
    await session.commit()
    return {"message": "Message deleted"}
