"""User routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.orm import User
from schemas.dto import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


@router.get("", response_model=list[UserResponse])
async def list_users(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID, user_update: UserUpdate, session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.name:
        user.name = user_update.name
    if user_update.email:
        user.email = user_update.email

    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(user_id: UUID, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(user)
    await session.commit()
    return {"message": "User deleted"}
