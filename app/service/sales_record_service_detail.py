from datetime import date
from sqlalchemy import select, func, cast, Integer, and_
from sqlalchemy.ext.asyncio import AsyncSession

from model.product import Product
from model.sales_record import SalesRecord


# ─────────────────────────────────────────
# 공통 헬퍼: 연도 → DATE 범위 조건
# extract() 대신 BETWEEN으로 인덱스 활용
# ─────────────────────────────────────────
def _year_range(year: int):
    return and_(
        SalesRecord.sold_at >= date(year, 1, 1),
        SalesRecord.sold_at < date(year + 1, 1, 1),   # < 로 경계 명확히
    )


# ─────────────────────────────────────────
# 1. 분기별 매출
# ─────────────────────────────────────────
async def find_quarterly_sales(db: AsyncSession, year: int) -> list[tuple]:
    """분기별 매출 합계 - 없는 분기는 0으로 채워서 반환"""
    result = await db.execute(
        select(
            # PostgreSQL: DATE_TRUNC 대신 CASE로 분기 계산 (이식성 높음)
            func.floor((func.extract("month", SalesRecord.sold_at) - 1) / 3 + 1)
               .cast(Integer).label("quarter"),
            func.sum(SalesRecord.sales_price).label("total_sales")
        )
        .where(_year_range(year))
        .group_by("quarter")
        .order_by("quarter")
    )
    rows = {int(r.quarter): int(r.total_sales) for r in result.all()}

    # 누락 분기 0으로 보정 (프론트 차트 대비)
    return [(q, rows.get(q, 0)) for q in range(1, 5)]


# ─────────────────────────────────────────
# 2. 월별 매출
# ─────────────────────────────────────────
async def find_monthly_sales(db: AsyncSession, year: int) -> list[tuple]:
    """월별 매출 합계 - 없는 달은 0으로 채워서 반환"""
    result = await db.execute(
        select(
            func.extract("month", SalesRecord.sold_at).cast(Integer).label("month"),
            func.sum(SalesRecord.sales_price).label("total_sales")
        )
        .where(_year_range(year))
        .group_by("month")
        .order_by("month")
    )
    rows = {int(r.month): int(r.total_sales) for r in result.all()}

    # 누락 월 0으로 보정
    return [(m, rows.get(m, 0)) for m in range(1, 13)]


# ─────────────────────────────────────────
# 3. 상품별 매출
# ─────────────────────────────────────────
async def find_product_sales(db: AsyncSession, year: int) -> list[tuple]:
    """상품별 매출 합계 (내림차순)"""
    total_sales = func.sum(SalesRecord.sales_price).label("total_sales")

    result = await db.execute(
        select(Product.name.label("product_name"), total_sales)
        .join(Product, SalesRecord.product_id == Product.id)
        .where(_year_range(year))
        .group_by(Product.id, Product.name)
        .order_by(func.sum(SalesRecord.sales_price).desc())  # label 참조는 DB마다 동작 달라 명시적으로 유지
    )
    return result.all()


# ─────────────────────────────────────────
# 4. 연 매출 합계
# ─────────────────────────────────────────
async def find_yearly_total(db: AsyncSession, year: int) -> int:
    result = await db.execute(
        select(func.sum(SalesRecord.sales_price).label("total_sales"))
        .where(_year_range(year))
    )
    row = result.one_or_none()
    return int(row.total_sales) if row and row.total_sales else 0


# ─────────────────────────────────────────
# 5. 연도 목록
# ─────────────────────────────────────────
async def find_available_years(db: AsyncSession) -> list[int]:
    year_col = func.extract("year", SalesRecord.sold_at).cast(Integer)

    result = await db.execute(
        select(year_col.label("year"))
        .group_by(year_col)      # label이 아닌 표현식 직접 참조
        .order_by(year_col.desc())
    )
    return [row.year for row in result.all()]


# ─────────────────────────────────────────
# 6. [선택] 대시보드용 통합 조회 - DB 왕복 1번
# ─────────────────────────────────────────
async def find_dashboard_stats(db: AsyncSession, year: int) -> dict:
    """
    분기별 + 월별 + 연간 합계를 쿼리 1번으로 처리.
    대시보드처럼 한 화면에 다 필요할 때 사용.
    """
    month_col = func.extract("month", SalesRecord.sold_at).cast(Integer)

    result = await db.execute(
        select(
            month_col.label("month"),
            func.floor((month_col - 1) / 3 + 1).cast(Integer).label("quarter"),
            func.sum(SalesRecord.sales_price).label("total_sales")
        )
        .where(_year_range(year))
        .group_by("month", "quarter")
        .order_by("month")
    )
    rows = result.all()

    monthly = {r.month: int(r.total_sales) for r in rows}
    quarterly: dict[int, int] = {}
    for r in rows:
        quarterly[r.quarter] = quarterly.get(r.quarter, 0) + int(r.total_sales)

    return {
        "year": year,
        "yearly_total": sum(monthly.values()),
        "monthly": [(m, monthly.get(m, 0)) for m in range(1, 13)],
        "quarterly": [(q, quarterly.get(q, 0)) for q in range(1, 5)],
    }