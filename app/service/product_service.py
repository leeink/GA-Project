import uuid
from sqlalchemy import select, insert, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from model.product import Product
from model.sales_record import SalesRecord
from model.product_stock import ProductStock

# 모든 상품 및 가용 재고 조회
async def find_all_product(db: AsyncSession):
    inventory_subquery = (
        select(ProductStock.product_id, func.sum(ProductStock.current_quantity).label("total_qty"))
        .where(ProductStock.status == 'NORMAL', ProductStock.expiration_date > func.now())
        .group_by(ProductStock.product_id).subquery()
    )
    query = select(Product, func.coalesce(inventory_subquery.c.total_qty, 0)).outerjoin(inventory_subquery, Product.id == inventory_subquery.c.product_id)
    result = await db.execute(query)
    products = []
    for row in result.all():
        p, qty = row
        p.total_avail_qty = qty
        products.append(p)
    return products

# 유저의 최신 주문 주소 조회
async def get_last_address(db: AsyncSession, user_id: uuid.UUID):
    query = select(SalesRecord.address).where(SalesRecord.user_id == user_id).order_by(desc(SalesRecord.id)).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()

# 주문 실행 (FIFO 재고 차감)
async def product_order(db: AsyncSession, dto, user_id: uuid.UUID):
    product_ids = list(dto.item.keys())
    result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    product_map = {p.id: p for p in result.scalars().all()}
    
    sales_records = []
    for p_id, requested_qty in dto.item.items():
        product = product_map.get(p_id)
        # 재고 차감 로직 생략(기존과 동일)
        sales_records.append({
            "product_id": p_id, "user_id": user_id, "quantity": requested_qty,
            "sales_price": product.cost * requested_qty, "address": dto.address
        })
    await db.execute(insert(SalesRecord).values(sales_records))
    await db.commit()
    return {"saved": True}