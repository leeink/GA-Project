from datetime import date
from sqlalchemy import select, func, cast, Integer, and_
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

# ─────────────────────────────────────────
# 공통 헬퍼: 2026년 이전 데이터 필터
# extract() 대신 범위 조건으로 인덱스 활용
# ─────────────────────────────────────────
def _before_current_year():
    """당해연도 데이터 제외 — 매년 코드 수정 불필요"""
    return SalesRecord.sold_at < date(date.today().year, 1, 1)


# ─────────────────────────────────────────
# 1. 연도별 총매출
# ─────────────────────────────────────────
async def selectYear_totalSales(db: AsyncSession) -> list:
    result = await db.execute(
        select(
            func.extract("year", SalesRecord.sold_at).cast(Integer).label("year"),
            func.sum(SalesRecord.sales_price).label("total_sales")
        )
        .where(_before_current_year())
        .group_by("year")
        .order_by("year")
    )
    return result.mappings().all()


# ─────────────────────────────────────────
# 2. TOP 5 — 판매량 + 매출액 한 번에 조회
# best5_count + best5_sales를 쿼리 1번으로 합산
# ─────────────────────────────────────────
async def best5_combined(db: AsyncSession) -> dict:
    """
    판매량 TOP5 + 매출액 TOP5를 DB 왕복 1번으로 처리.
    두 랭킹 모두 필요한 대시보드에서 사용.
    """
    result = await db.execute(
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.sum(SalesRecord.quantity).label("total_quantity"),
            func.sum(SalesRecord.sales_price).label("total_sales")
        )
        .join(SalesRecord.product)
        .where(_before_current_year())
        .group_by(Product.id, Product.name)   # id 기준으로 안전하게 group
    )
    rows = result.mappings().all()

    # Python에서 정렬 + 슬라이싱 (DB 왕복 추가 없이)
    by_quantity = sorted(rows, key=lambda r: r["total_quantity"], reverse=True)[:5]
    by_sales    = sorted(rows, key=lambda r: r["total_sales"],    reverse=True)[:5]

    return {
        "best5_count": by_quantity,
        "best5_sales": by_sales,
    }


# ─────────────────────────────────────────
# 기존 인터페이스 유지가 필요할 때만 사용
# (best5_combined 사용 권장)
# ─────────────────────────────────────────
async def best5_count(db: AsyncSession) -> list:
    result = await db.execute(
        select(
            Product.name.label("product_name"),
            func.sum(SalesRecord.quantity).label("total_quantity")
        )
        .join(SalesRecord.product)
        .where(_before_current_year())
        .group_by(Product.id, Product.name)
        .order_by(func.sum(SalesRecord.quantity).desc())
        .limit(5)
    )
    return result.mappings().all()


async def best5_sales(db: AsyncSession) -> list:
    result = await db.execute(
        select(
            Product.name.label("product_name"),
            func.sum(SalesRecord.sales_price).label("total_sales")
        )
        .join(SalesRecord.product)
        .where(_before_current_year())
        .group_by(Product.id, Product.name)
        .order_by(func.sum(SalesRecord.sales_price).desc())
        .limit(5)
    )
    return result.mappings().all()