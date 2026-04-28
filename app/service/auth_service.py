import secrets
from datetime import datetime, timedelta, timezone

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from core.config import settings
from core.exceptions import BadRequestException
from core.security import verify_password, create_access_token
from schema.auth_schema import TokenResponse
from model.refreshtoken import RefreshToken
from service.user_service import find_user_by_email, find_user_by_id


async def login(db: AsyncSession, data: OAuth2PasswordRequestForm) -> TokenResponse:
    user = await find_user_by_email(db, data.username)

    # Invalid email or password or Incorrect password
    if not user or not verify_password(data.password, user.password_hash):
        raise BadRequestException("Invalid email or Incorrect password")
    # Account is not active
    if not user.is_active:
        raise BadRequestException("Account is not active")

    # Remove Existing Refresh Token
    await db.execute(
        delete(RefreshToken)
        .where(RefreshToken.user_id == user.id)
    )

    raw_refresh_token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(
        user_id = user.id,
        token = raw_refresh_token,
        expires_at = expires_at,
    ))

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=raw_refresh_token,
    )

async def refresh_token(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
    # Select Refresh Token

    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token == refresh_token_str)
    )
    token = result.scalar_one_or_none()

    if not token:
        raise BadRequestException("Invalid refresh token")
    if token.expires_at < datetime.now(timezone.utc):
        await db.delete(token)
        raise BadRequestException("Refresh token has expired")

    user = await find_user_by_id(db, token.user_id)
    if not user or not user.is_active:
        raise BadRequestException("Invalid user")

    await db.delete(token)

    new_refresh_token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(
        user_id = user.id,
        token = new_refresh_token,
        expires_at = expires_at,
    ))

    return TokenResponse(
        access_token = create_access_token(str(user.id)),
        refresh_token=new_refresh_token,
    )

async def logout(db: AsyncSession, refresh_token_str: str) -> None:
    await db.execute(
        delete(RefreshToken)
        .where(RefreshToken.token == refresh_token_str)
    )