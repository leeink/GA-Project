import uuid

from core.exceptions import HTTPException
from sqlalchemy import select, insert,func
from sqlalchemy.ext.asyncio import AsyncSession

from model.product import Product, CategoryType
from model.sales_record import SalesRecord
from model.product_stock import ProductStock
from schema.order_schema import OrderSchema


# 모든 상품 가져오기
async def find_all_product(db: AsyncSession):
    result = await db.execute(select(Product))
    return result.scalars().all()


# 상품명 검색 가져오기
async def find_product_search(db: AsyncSession, name: str):
    result = await db.execute(
        select(Product).where(Product.name.ilike(f"%{name}%"))
    )
    return result.scalars().all()


# 카테고리 별로 가져오기
async def find_product_by_category(db: AsyncSession, category: str):
    result = await db.execute(
        select(Product).where(Product.category == CategoryType(category))
    )
    return result.scalars().all()

# 상품 주문
async def product_order(db: AsyncSession, dto: OrderSchema, user_id: uuid.UUID | str):
    # 1. 모든 product_id 추출
    product_ids = list(dto.item.keys())

    # 2. 상품 정보 및 '가용 재고 합계' 한 번에 조회
    # product_stock에서 NORMAL 상태이며 유통기한이 남은 것들만 합산
    inventory_query = (
        select(
            Product.id,
            Product.cost,
            func.coalesce(func.sum(ProductStock.current_quantity), 0).label("total_avail_qty")
        )
        .outerjoin(ProductStock, (Product.id == ProductStock.product_id) &
                   (ProductStock.status == 'NORMAL') &
                   (ProductStock.expiration_date > func.now()))
        .where(Product.id.in_(product_ids))
        .group_by(Product.id)
    )

    result = await db.execute(inventory_query)
    product_data = {row.id: row for row in result.all()}

    # 3. 상품 존재 여부 및 재고 수량 검증
    sales_records = []
    for p_id, requested_qty in dto.item.items():
        if p_id not in product_data:
            raise HTTPException(status_code=404, detail=f"상품 없음: {p_id}")

        product = product_data[p_id]
        if product.total_avail_qty < requested_qty:
            raise HTTPException(
                status_code=400,
                detail=f"재고 부족: {p_id} (요청: {requested_qty}, 잔여: {product.total_avail_qty})"
            )

        # 4. 재고 차감 (FIFO: 선입선출 로직)
        # 해당 상품의 개별 재고 묶음들을 유통기한 순으로 가져옴
        stock_result = await db.execute(
            select(ProductStock)
            .where(
                ProductStock.product_id == p_id,
                ProductStock.status == 'NORMAL',
                ProductStock.expiration_date > func.now(),
                ProductStock.current_quantity > 0
            )
            .order_by(ProductStock.expiration_date.asc())
        )
        stocks = stock_result.scalars().all()

        remaining_to_deduct = requested_qty
        for stock in stocks:
            if remaining_to_deduct <= 0:
                break

            if stock.current_quantity >= remaining_to_deduct:
                # 현재 묶음에서 모두 차감 가능
                stock.current_quantity -= remaining_to_deduct
                remaining_to_deduct = 0
            else:
                # 현재 묶음을 다 쓰고 다음 묶음으로 넘어가야 함
                remaining_to_deduct -= stock.current_quantity
                stock.current_quantity = 0

        # 5. 판매 기록 데이터 준비
        sales_records.append({
            "product_id": p_id,
            "user_id": user_id,
            "quantity": requested_qty,
            "sales_price": product.cost * requested_qty,
            "address": dto.address,
        })

    # 6. Bulk Insert (판매 기록 생성)
    if sales_records:
        await db.execute(insert(SalesRecord).values(sales_records))

    # 7. 트랜잭션 확정 (재고 차감과 판매 기록 생성이 원자적으로 처리됨)
    await db.commit()
    return {"message": "주문 성공"}