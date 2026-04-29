from core.exceptions import HTTPException
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from model.product import Product, CategoryType
from model.sales_record import SalesRecord
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
async def product_order(db: AsyncSession, dto: OrderSchema):
    # 1. 모든 product_id를 한 번에 추출
    product_ids = list(dto.item.keys())

    # 2. 필요한 상품 정보를 한 번에 조회 (N+1 문제 해결)
    result = await db.execute(
        select(Product).where(Product.id.in_(product_ids))
    )
    products = {p.id: p for p in result.scalars().all()}

    # 3. 모든 상품이 존재하는지 검증
    if len(products) != len(product_ids):
        missing = set(product_ids) - set(products.keys())
        raise HTTPException(status_code=404, detail=f"Products not found: {missing}")

    # 4. Insert할 데이터를 리스트로 준비
    sales_records = []
    for p_id, qty in dto.item.items():
        product = products[p_id]
        sales_records.append({
            "product_id": p_id,
            "user_id": "0011d302-ecd8-4b91-ad7d-a74f635b93a5",
            "quantity": qty,
            "sales_price": product.cost * qty,
            "address": dto.address,
        })

    # 5. 한 번의 쿼리로 대량 삽입 (Bulk Insert)
    if sales_records:
        await db.execute(insert(SalesRecord).values(sales_records))

    # 6. 트랜잭션 확정
    await db.commit()