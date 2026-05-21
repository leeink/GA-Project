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


async def add_to_cart(
    db: AsyncSession,
    user_id: uuid.UUID,
    product_id: uuid.UUID,
    quantity: int,
):
    # 1번: 상품 존재 확인 (lock 불필요)
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    # 2번: 재고 조회 (lock)
    stock = await get_available_stock(db, product_id, lock=True)

    # 3번: 기존 카트 아이템 조회 (lock)
    result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id, Cart.product_id == product_id)
        .with_for_update()
    )
    cart_item = result.scalar_one_or_none()

    next_quantity = (cart_item.cart_quantity + quantity) if cart_item else quantity
    if next_quantity > stock:
        raise HTTPException(status_code=400, detail="재고가 부족합니다.")

    if cart_item:
        cart_item.cart_quantity = next_quantity
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
# 수량 변경 — 왕복 3번 → 2번
# ─────────────────────────────────────────
async def update_cart_quantity(
    db: AsyncSession,
    user_id: uuid.UUID,
    cart_id: uuid.UUID,
    quantity: int,
):
    # 1번: 카트 아이템 + 재고 한 번에
    result = await db.execute(
        select(Cart)
        .where(Cart.id == cart_id, Cart.user_id == user_id)
        .with_for_update()
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        raise HTTPException(status_code=404, detail="장바구니 상품을 찾을 수 없습니다.")

    # 2번: 재고 확인 (lock)
    stock = await get_available_stock(db, cart_item.product_id, lock=True)
    if quantity > stock:
        raise HTTPException(status_code=400, detail="재고가 부족합니다.")

    cart_item.cart_quantity = quantity
    cart_item.current_time = func.now()

    await db.flush()
    return await get_user_cart(db, user_id)         # 3번: 최종 목록


# ─────────────────────────────────────────
# 단일 삭제
# ─────────────────────────────────────────
async def delete_cart_item(
    db: AsyncSession,
    user_id: uuid.UUID,
    cart_id: uuid.UUID,
):
    await db.execute(
        delete(Cart).where(
            Cart.id == cart_id,
            Cart.user_id == user_id,
        )
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