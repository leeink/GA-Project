from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, extract, func

from model.sales_record import SalesRecord
from model.product import Product


async def find_quarterly_sales(db: AsyncSession, year: str):
    """분기별 매출 합계 (1~4분기 전체)"""
    result = await db.execute(
        select(
            extract("quarter", SalesRecord.sold_at).label("quarter"),
            func.sum(SalesRecord.sales_price).label("total_sales")
        )
        .where(extract("year", SalesRecord.sold_at) == int(year))
        .group_by(extract("quarter", SalesRecord.sold_at))
        .order_by("quarter")
    )
    return result.all()  # [(quarter, total_sales), ...]


async def find_monthly_sales(db: AsyncSession, year: str):
    """월별 매출 합계 (1~12월)"""
    result = await db.execute(
        select(
            extract("month", SalesRecord.sold_at).label("month"),
            func.sum(SalesRecord.sales_price).label("total_sales")
        )
        .where(extract("year", SalesRecord.sold_at) == int(year))
        .group_by(extract("month", SalesRecord.sold_at))
        .order_by("month")
    )
    return result.all()  # [(month, total_sales), ...]


async def find_product_sales(db: AsyncSession, year: str):
    """상품별 매출 합계 (내림차순)"""
    result = await db.execute(
        select(
            Product.name.label("product_name"),
            func.sum(SalesRecord.sales_price).label("total_sales")
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .where(extract("year", SalesRecord.sold_at) == int(year))
        .group_by(Product.id, Product.name)
        .order_by(func.sum(SalesRecord.sales_price).desc())
    )
    return result.all()  # [(product_name, total_sales), ...]


async def find_yearly_total(db: AsyncSession, year: str):
    """연 매출 합계"""
    result = await db.execute(
        select(
            func.sum(SalesRecord.sales_price).label("total_sales")
        )
        .where(extract("year", SalesRecord.sold_at) == int(year))
    )
    row = result.one_or_none()
    return int(row.total_sales) if row and row.total_sales else 0

async def find_available_years(db: AsyncSession) -> list[int]:
    """매출 데이터가 있는 연도 목록 (내림차순)"""
    result = await db.execute(
        select(
            extract("year", SalesRecord.sold_at).label("year")
        )
        .group_by(extract("year", SalesRecord.sold_at))
        .order_by(extract("year", SalesRecord.sold_at).desc())
    )
    return [int(row.year) for row in result.all()]