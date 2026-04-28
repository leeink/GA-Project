import uuid
from typing import Any, Sequence

from core.security import hash_password
from model.user import User
from schema.user_schema import UserCreateRequest
from core.exceptions import *
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def find_all_user(db: AsyncSession) -> Sequence[Any]:
    result = await db.execute(
        select(User)
    )

    return result.scalars().all()

async def find_user_by_id(db: AsyncSession, user_id: str | uuid.UUID) -> User | None:
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
    )

    return result.scalar_one_or_none()

async def find_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User)
        .where(User.email == email)
    )

    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, data: UserCreateRequest) -> User:
    # check duplicate email
    if await find_user_by_email(db, data.email):
        raise ConflictException("Email already exists")

    user = User(
        email = data.email,
        password_hash = hash_password(data.password),
        nickname = data.nickname,
    )

    db.add(user)
    await db.flush()

    return user