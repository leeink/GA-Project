import secrets, uuid
from datetime import datetime, timedelta, timezone

from fastapi.security import OAuth2PasswordRequestForm
from core.config import settings
from core.exceptions import BadRequestException
from core.security import verify_password, create_access_token
from schema.auth_schema import TokenResponse
from model.refreshtoken import RefreshToken
from service.user_service import find_user_by_email, find_user_by_id

from fastapi import HTTPException, status
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from model.sales_record import SalesRecord


async def login(db: AsyncSession, data: OAuth2PasswordRequestForm):
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
    ), user.id

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


async def find_completed_orders_by_user(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(SalesRecord)
        .options(joinedload(SalesRecord.product))
        .where(SalesRecord.user_id == user_id)
        .order_by(SalesRecord.sold_at.desc())
    )
    records = result.scalars().all()

    return [
        {
            "id": r.id,
            "sold_at": r.sold_at,
            "product_id": r.product_id,
            "product_name": r.product.name if r.product else None,
            "quantity": r.quantity,
            "sales_price": r.sales_price,
            "address": r.address,
        }
        for r in records
    ]


async def update_completed_order_quantity(
        db: AsyncSession,
        user_id: uuid.UUID,
        order_id: uuid.UUID,
        quantity: int) -> None:
    if quantity < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수량은 1 이상이어야 합니다.",
        )

    result = await db.execute(
        select(SalesRecord).where(
            SalesRecord.id == order_id,
            SalesRecord.user_id == user_id,
        )
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="주문을 찾을 수 없습니다.",
        )

    await db.execute(
        update(SalesRecord)
        .where(SalesRecord.id == order_id, SalesRecord.user_id == user_id)
        .values(quantity=quantity)
    )
    await db.commit()


async def update_completed_order_address(
        db: AsyncSession,
        user_id: uuid.UUID,
        address: str) -> None:
    if not address or not address.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="주소를 입력해 주세요.",
        )

    await db.execute(
        update(SalesRecord)
        .where(SalesRecord.user_id == user_id)
        .values(address=address.strip())
    )
    await db.commit()


async def delete_completed_order(
        db: AsyncSession,
        user_id: uuid.UUID,
        order_id: uuid.UUID) -> None:
    result = await db.execute(
        select(SalesRecord).where(
            SalesRecord.id == order_id,
            SalesRecord.user_id == user_id,
        )
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="주문을 찾을 수 없습니다.",
        )

    await db.execute(
        delete(SalesRecord).where(
            SalesRecord.id == order_id,
            SalesRecord.user_id == user_id,
        )
    )
    await db.commit()