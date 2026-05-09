"""Conversation routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.orm import Conversation
from schemas.dto import ConversationCreate, ConversationUpdate, ConversationResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    conv: ConversationCreate, session: AsyncSession = Depends(get_db)
):
    db_conv = Conversation(user_id=conv.user_id, title=conv.title)
    session.add(db_conv)
    await session.commit()
    await session.refresh(db_conv)
    return db_conv


@router.get("/user/{user_id}", response_model=list[ConversationResponse])
async def list_user_conversations(
    user_id: UUID, session: AsyncSession = Depends(get_db)
):
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID, session: AsyncSession = Depends(get_db)
):
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    conv_update: ConversationUpdate,
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conv_update.title:
        conv.title = conv_update.title

    await session.commit()
    await session.refresh(conv)
    return conv


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID, session: AsyncSession = Depends(get_db)
):
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await session.delete(conv)
    await session.commit()
    return {"message": "Conversation deleted"}
