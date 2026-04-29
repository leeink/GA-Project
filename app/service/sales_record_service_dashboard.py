from sqlalchemy import select, extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from model.sales_record import SalesRecord
from model.product import Product

# https://supabase.com
# SclesRecord
# id : 판매기록 고유id
# sold_at : 팔린시점(년/월/일/시간)
# product_id : 상품고유코드
# user_id : 유저id
# quantity : 개수
# sales_price : 판매가격(이미계산된가격)
# product : 외부 ORM에서 땡겨온 상품이름


#연도별 총매출
async def selectYear_totalSales(db: AsyncSession):
    DTO = (
        select(
            extract('year', SalesRecord.sold_at).label('year'),
            func.sum(SalesRecord.sales_price).label('total_sales')
        )
        .where(extract('year', SalesRecord.sold_at) < 2026) #26년자료 제외
        .group_by(extract('year', SalesRecord.sold_at))
        .order_by(extract('year', SalesRecord.sold_at))
    )
    result = await db.execute(DTO)
    return result.mappings().all()

#많이 팔린 상품 TOP 5 (판매량 기준)
async def best5_count(db: AsyncSession):
    DTO = (
        select(
            Product.name.label('product_name'), # 상품명 사용
            func.sum(SalesRecord.quantity).label('total_quantity')
        )
        .join(SalesRecord.product)
        .where(extract('year', SalesRecord.sold_at) < 2026) #26년자료 제외
        .group_by(Product.name)
        .order_by(func.sum(SalesRecord.quantity).desc()) #내림
        .limit(5) #순위
    )
    result = await db.execute(DTO)
    return result.mappings().all()

#매출 순위 상품 TOP 5 (총액 기준)
async def best5_sales(db: AsyncSession):
    DTO = (
        select(
            Product.name.label('product_name'),
            func.sum(SalesRecord.sales_price).label('total_sales')
        )
        .join(SalesRecord.product)
        .where(extract('year', SalesRecord.sold_at) < 2026)
        .group_by(Product.name)
         .order_by(func.sum(SalesRecord.sales_price).desc()) #내림
        .limit(5)
    )
    result = await db.execute(DTO)
    return result.mappings().all()

#연도별 매출[타사비교] 비교 예정