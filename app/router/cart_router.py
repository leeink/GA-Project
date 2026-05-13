from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user_from_cookie
from schema.cart_schema import CartCreate, CartItemResponse, CartUpdate
from service import cart_service

router = APIRouter(prefix="/api/cart", tags=["cart"])


async def require_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return current_user


async def to_response(db: AsyncSession, items):
    responses = []
    for item in items:
        stock = await cart_service.get_available_stock(db, item.product_id)
        responses.append(
            CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                cart_quantity=item.cart_quantity,
                product_name=item.product.name,
                product_price=item.product.cost,
                stock=stock,
            )
        )
    return responses


@router.get("/", response_model=list[CartItemResponse])
async def read_cart(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    items = await cart_service.get_user_cart(db, current_user.id)
    return await to_response(db, items)


@router.post("/add", response_model=list[CartItemResponse])
async def add_cart(
    data: CartCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    items = await cart_service.add_to_cart(
        db,
        current_user.id,
        data.product_id,
        data.quantity,
    )
    return await to_response(db, items)


@router.patch("/{cart_id}", response_model=list[CartItemResponse])
async def update_cart(
    cart_id: str,
    data: CartUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    items = await cart_service.update_cart_quantity(
        db,
        current_user.id,
        cart_id,
        data.quantity,
    )
    return await to_response(db, items)


@router.delete("/{cart_id}", response_model=list[CartItemResponse])
async def delete_cart(
    cart_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    items = await cart_service.delete_cart_item(db, current_user.id, cart_id)
    return await to_response(db, items)


@router.delete("/", response_model=list[CartItemResponse])
async def clear_cart(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    items = await cart_service.clear_user_cart(db, current_user.id)
    return await to_response(db, items)
