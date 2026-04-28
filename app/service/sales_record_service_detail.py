from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, extract, func

from model.sales_record import SalesRecord


async def find_sales_record_by_quarter(db: AsyncSession, year: str, quarter: int = 1):
    result = await db.execute(
        select(
            extract("quarter", SalesRecord.sold_at).label("quarter"),
            func.sum(SalesRecord.sales_price).label("total_sales")
        )
        .where(extract("year", SalesRecord.sold_at) == year)
        .where(extract("quarter", SalesRecord.sold_at) == quarter)
        .group_by(
            extract("quarter", SalesRecord.sold_at)
        )
        .order_by("total_sales")
    )
    return result.all()