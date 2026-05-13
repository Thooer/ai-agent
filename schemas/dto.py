"""Pydantic schemas for request/response models."""

import json
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    created_at: datetime


class ConversationCreate(BaseModel):
    user_id: UUID
    title: Optional[str] = "New Conversation"


class ConversationUpdate(BaseModel):
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    created_at: datetime


class MessageCreate(BaseModel):
    conversation_id: UUID
    role: str
    content: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    conversation_id: Optional[UUID] = None
    use_rag: bool = True


# SSE event schema — type-based, no legacy format
class SseDelta(BaseModel):
    type: Literal["delta"] = "delta"
    content: str


class SseDone(BaseModel):
    type: Literal["done"] = "done"


class SseError(BaseModel):
    type: Literal["error"] = "error"
    message: str


def sse(model: BaseModel) -> str:
    return f"data: {model.model_dump_json()}\n\n"
