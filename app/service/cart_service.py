import uuid

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from model.cart import Cart
from model.product import Product
from model.product_stock import ProductStock


async def get_available_stock(db: AsyncSession, product_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(ProductStock.current_quantity), 0))
        .where(
            ProductStock.product_id == product_id,
            ProductStock.status == "NORMAL",
            ProductStock.expiration_date > func.now(),
        )
    )
    return result.scalar_one()


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
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    stock = await get_available_stock(db, product_id)

    result = await db.execute(
        select(Cart).where(
            Cart.user_id == user_id,
            Cart.product_id == product_id,
        )
    )
    cart_item = result.scalar_one_or_none()

    next_quantity = quantity
    if cart_item:
        next_quantity = cart_item.cart_quantity + quantity

    if next_quantity > stock:
        raise HTTPException(status_code=400, detail="재고가 부족합니다.")

    if cart_item:
        cart_item.cart_quantity = next_quantity
    else:
        db.add(
            Cart(
                user_id=user_id,
                product_id=product_id,
                cart_quantity=quantity,
            )
        )

    await db.flush()
    return await get_user_cart(db, user_id)


async def update_cart_quantity(
    db: AsyncSession,
    user_id: uuid.UUID,
    cart_id: uuid.UUID,
    quantity: int,
):
    result = await db.execute(
        select(Cart).where(
            Cart.id == cart_id,
            Cart.user_id == user_id,
        )
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=404, detail="장바구니 상품을 찾을 수 없습니다.")

    stock = await get_available_stock(db, cart_item.product_id)
    if quantity > stock:
        raise HTTPException(status_code=400, detail="재고가 부족합니다.")

    cart_item.cart_quantity = quantity
    await db.flush()
    return await get_user_cart(db, user_id)


async def delete_cart_item(db: AsyncSession, user_id: uuid.UUID, cart_id: uuid.UUID):
    await db.execute(
        delete(Cart).where(
            Cart.id == cart_id,
            Cart.user_id == user_id,
        )
    )
    await db.flush()
    return await get_user_cart(db, user_id)


async def clear_user_cart(db: AsyncSession, user_id: uuid.UUID):
    await db.execute(delete(Cart).where(Cart.user_id == user_id))
    await db.flush()
    return []
