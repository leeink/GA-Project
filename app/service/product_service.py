import uuid
from core.exceptions import HTTPException
from sqlalchemy import select, insert, func, desc, delete, asc
from sqlalchemy.orm import load_only
from sqlalchemy.ext.asyncio import AsyncSession
from model.product import Product
from model.sales_record import SalesRecord
from model.product_stock import ProductStock
from model.cart import Cart

# ─────────────────────────────────────────
# 1. 전체 상품 조회 + 재고 합산
# ─────────────────────────────────────────
async def find_all_product(db: AsyncSession):
    # NamedTuple 방식으로 받아서 ORM 객체 오염 방지
    inventory_subquery = (
        select(
            ProductStock.product_id,
            func.sum(ProductStock.current_quantity).label("total_qty")
        )
        .where(
            ProductStock.status == "NORMAL",
            ProductStock.expiration_date > func.now()
        )
        .group_by(ProductStock.product_id)
        .subquery()
    )

    query = (
        select(
            Product,
            func.coalesce(inventory_subquery.c.total_qty, 0).label("total_avail_qty")
        )
        .outerjoin(inventory_subquery, Product.id == inventory_subquery.c.product_id)
        .order_by(Product.id)          # 페이지네이션 대비 정렬 고정
        .options(load_only(            # 필요한 컬럼만 SELECT
            Product.id,
            Product.name,
            Product.cost,
        ))
    )

    result = await db.execute(query)
    rows = result.all()  # [(Product, qty), ...]

    # dataclass / pydantic 변환 시 ORM 객체 안 건드림
    return [
        {**row.Product.__dict__, "total_avail_qty": int(row.total_avail_qty)}
        for row in rows
    ]


# ─────────────────────────────────────────
# 2. 유저 최신 주문 주소
# ─────────────────────────────────────────
async def get_last_address(db: AsyncSession, user_id: uuid.UUID) -> str | None:
    # 기존도 나쁘지 않지만 id 대신 sold_at 기준이 더 명확
    query = (
        select(SalesRecord.address)
        .where(SalesRecord.user_id == user_id)
        .order_by(desc(SalesRecord.sold_at))
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


# ─────────────────────────────────────────
# 3. 주문 실행 - FIFO 재고 차감 포함
# ─────────────────────────────────────────
async def product_order(db: AsyncSession, dto, user_id: uuid.UUID):
    product_ids = list(dto.item.keys())

    # ① 상품 + 재고 한 번에 로드 (N+1 방지)
    result = await db.execute(
        select(Product)
        .where(Product.id.in_(product_ids))
    )
    product_map = {p.id: p for p in result.scalars().all()}

    # ② FIFO 재고 차감
    for p_id, requested_qty in dto.item.items():
        remaining = requested_qty

        stocks_result = await db.execute(
            select(ProductStock)
            .where(
                ProductStock.product_id == p_id,
                ProductStock.status == "NORMAL",
                ProductStock.expiration_date > func.now(),
                ProductStock.current_quantity > 0,
            )
            .order_by(asc(ProductStock.expiration_date))  # FIFO: 가까운 유통기한 먼저
            .with_for_update()
        )
        stocks = stocks_result.scalars().all()

        for stock in stocks:
            if remaining <= 0:
                break
            deduct = min(stock.current_quantity, remaining)
            stock.current_quantity -= deduct
            remaining -= deduct
            if stock.current_quantity == 0:
                stock.status = "EXHAUSTED"

        if remaining > 0:
            raise HTTPException(
                status_code=409,
                detail=f"재고 부족: product_id={p_id}, 부족량={remaining}"
            )

    # ③ SalesRecord bulk insert + Cart 삭제를 한 트랜잭션에
    sales_records = [
        {
            "product_id": p_id,
            "user_id": user_id,
            "quantity": qty,
            "sales_price": product_map[p_id].cost * qty,
            "address": dto.address,
        }
        for p_id, qty in dto.item.items()
    ]

    await db.execute(insert(SalesRecord).values(sales_records))
    await db.execute(
        delete(Cart).where(Cart.user_id == user_id)
    )
    await db.commit()
    return {"saved": True}