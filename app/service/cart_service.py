import uuid
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from model.cart import Cart
from model.product import Product
from model.product_stock import ProductStock


# ─────────────────────────────────────────
# 재고 조회 (with_for_update 옵션 추가)
# ─────────────────────────────────────────
async def get_available_stock(
    db: AsyncSession,
    product_id: uuid.UUID,
    lock: bool = False,
) -> int:
    if lock:
        # 집계 쿼리에는 FOR UPDATE 불가
        # → 개별 row를 lock 걸고 Python에서 합산
        result = await db.execute(
            select(ProductStock.current_quantity)
            .where(
                ProductStock.product_id == product_id,
                ProductStock.status == "NORMAL",
                ProductStock.expiration_date > func.now(),
            )
            .with_for_update()
        )
        return sum(row[0] for row in result.all())
    else:
        result = await db.execute(
            select(func.coalesce(func.sum(ProductStock.current_quantity), 0))
            .where(
                ProductStock.product_id == product_id,
                ProductStock.status == "NORMAL",
                ProductStock.expiration_date > func.now(),
            )
        )
        return result.scalar_one()


# ─────────────────────────────────────────
# 카트 조회
# ─────────────────────────────────────────
async def get_user_cart(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.product))
        .where(Cart.user_id == user_id)
        .order_by(Cart.id)
    )
    return result.scalars().all()


# ─────────────────────────────────────────
# 카트 담기
# ─────────────────────────────────────────
async def add_to_cart(
    db: AsyncSession,
    user_id: uuid.UUID,
    product_id: uuid.UUID,
    quantity: int,
):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    result = await db.execute(
        select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    )
    cart_item = result.scalar_one_or_none()

    if cart_item:
        cart_item.cart_quantity += quantity
        cart_item.current_time = func.now()
    else:
        db.add(Cart(
            user_id=user_id,
            product_id=product_id,
            cart_quantity=quantity,
            current_time=func.now(),
        ))

    await db.flush()
    return await get_user_cart(db, user_id)


# ─────────────────────────────────────────
# 수량 변경
# ─────────────────────────────────────────
async def update_cart_quantity(
    db: AsyncSession,
    user_id: uuid.UUID,
    cart_id: uuid.UUID,
    quantity: int,
):
    result = await db.execute(
        select(Cart).where(Cart.id == cart_id, Cart.user_id == user_id)
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        raise HTTPException(status_code=404, detail="장바구니 상품을 찾을 수 없습니다.")

    cart_item.cart_quantity = quantity
    cart_item.current_time = func.now()

    await db.flush()
    return await get_user_cart(db, user_id)


# ─────────────────────────────────────────
# 단일 삭제
# ─────────────────────────────────────────
async def delete_cart_item(
    db: AsyncSession,
    user_id: uuid.UUID,
    cart_id: uuid.UUID,
):
    await db.execute(
        delete(Cart).where(Cart.id == cart_id, Cart.user_id == user_id)
    )
    await db.flush()
    return await get_user_cart(db, user_id)


# ─────────────────────────────────────────
# 전체 비우기
# ─────────────────────────────────────────
async def clear_user_cart(db: AsyncSession, user_id: uuid.UUID):
    await db.execute(delete(Cart).where(Cart.user_id == user_id))
    await db.flush()
    return []