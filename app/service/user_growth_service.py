# [SERVICE] 유저 성장률 비교 데이터 조회 (전년 vs 당해)
import asyncio
from datetime import date

from sqlalchemy import select, func, Integer, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from model.user import User


# ─────────────────────────────────────────
# 공통 헬퍼: 2개 연도 범위 조건
# extract().in_() 대신 OR(BETWEEN) → 인덱스 활용
# ─────────────────────────────────────────
def _two_year_range(curr_year: int):
    """당해 + 전년도 범위 필터"""
    prev_year = curr_year - 1
    return or_(
        and_(
            User.created_at >= date(prev_year, 1, 1),
            User.created_at <  date(curr_year, 1, 1),
        ),
        and_(
            User.created_at >= date(curr_year, 1, 1),
            User.created_at <  date(curr_year + 1, 1, 1),
        ),
    )


# ─────────────────────────────────────────
# 1. 전체 고객 수
# ─────────────────────────────────────────
async def find_total_user_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(User.id)))
    return result.scalar() or 0


# ─────────────────────────────────────────
# 2. 연간 성장률
# ─────────────────────────────────────────
async def find_yearly_user_growth(db: AsyncSession, year: int) -> dict:
    prev_year = year - 1

    result = await db.execute(
        select(
            func.extract("year", User.created_at).cast(Integer).label("year"),
            func.count(User.id).label("user_count")
        )
        .where(_two_year_range(year))
        .group_by("year")
    )
    data = {row.year: row.user_count for row in result.all()}

    curr_count = data.get(year, 0)
    prev_count = data.get(prev_year, 0)
    growth_rate = round((curr_count - prev_count) / prev_count * 100, 2) if prev_count > 0 else None

    return {
        "current_year":   year,
        "previous_year":  prev_year,
        "current_count":  curr_count,
        "previous_count": prev_count,
        "growth_rate":    growth_rate,   # None = 전년 데이터 없음 (0과 구분)
    }


# ─────────────────────────────────────────
# 3. 공통 비교 조회 내부 함수
# 분기/월 모두 이 함수로 처리 (중복 제거)
# ─────────────────────────────────────────
async def _fetch_period_compare(
    db: AsyncSession,
    year: int,
    period_extract: str,       # "quarter" | "month"
    period_range: range,       # range(1, 5) | range(1, 13)
    period_key: str,           # "quarter" | "month"
) -> list[dict]:
    prev_year = year - 1

    result = await db.execute(
        select(
            func.extract("year", User.created_at).cast(Integer).label("year"),
            func.extract(period_extract, User.created_at).cast(Integer).label("period"),
            func.count(User.id).label("count")
        )
        .where(_two_year_range(year))
        .group_by("year", "period")
        .order_by("year", "period")
    )

    stats: dict[int, dict[int, int]] = {prev_year: {}, year: {}}
    for row in result.all():
        stats[row.year][row.period] = row.count

    return [
        {
            period_key:   p,
            "prev_count": stats[prev_year].get(p, 0),
            "curr_count": stats[year].get(p, 0),
            # 증감률을 여기서 같이 계산해두면 프론트 연산 불필요
            "growth_rate": round(
                (stats[year].get(p, 0) - stats[prev_year].get(p, 0))
                / stats[prev_year].get(p, 0) * 100, 2
            ) if stats[prev_year].get(p, 0) > 0 else None,
        }
        for p in period_range
    ]


# ─────────────────────────────────────────
# 4. 분기별 비교
# ─────────────────────────────────────────
async def find_quarterly_compare_data(db: AsyncSession, year: int) -> list[dict]:
    return await _fetch_period_compare(
        db, year,
        period_extract="quarter",
        period_range=range(1, 5),
        period_key="quarter",
    )


# ─────────────────────────────────────────
# 5. 월별 비교
# ─────────────────────────────────────────
async def find_monthly_compare_data(db: AsyncSession, year: int) -> list[dict]:
    return await _fetch_period_compare(
        db, year,
        period_extract="month",
        period_range=range(1, 13),
        period_key="month",
    )


# ─────────────────────────────────────────
# 6. [선택] 대시보드용 통합 조회 — DB 왕복 2번으로 전체 처리
# find_yearly + find_quarterly + find_monthly 를 한꺼번에
# ─────────────────────────────────────────
async def find_user_growth_dashboard(db: AsyncSession, year: int) -> dict:
    """
    연간·분기·월별 성장률을 DB 왕복 2번으로 처리.
    (전체 유저 수 1번 + 비교 데이터 1번)
    """
    total, monthly = await asyncio.gather(
        find_total_user_count(db),
        _fetch_period_compare(db, year, "month", range(1, 13), "month"),
    )

    prev_year = year - 1
    curr_total  = sum(r["curr_count"] for r in monthly)
    prev_total  = sum(r["prev_count"] for r in monthly)
    growth_rate = round((curr_total - prev_total) / prev_total * 100, 2) if prev_total > 0 else None

    # 분기 집계는 월 데이터에서 Python으로 계산 (추가 쿼리 불필요)
    quarterly: dict[int, dict] = {q: {"prev": 0, "curr": 0} for q in range(1, 5)}
    for r in monthly:
        q = (r["month"] - 1) // 3 + 1
        quarterly[q]["prev"] += r["prev_count"]
        quarterly[q]["curr"] += r["curr_count"]

    return {
        "total_users": total,
        "yearly": {
            "current_count":  curr_total,
            "previous_count": prev_total,
            "growth_rate":    growth_rate,
        },
        "quarterly": [
            {
                "quarter":    q,
                "prev_count": v["prev"],
                "curr_count": v["curr"],
                "growth_rate": round((v["curr"] - v["prev"]) / v["prev"] * 100, 2) if v["prev"] > 0 else None,
            }
            for q, v in quarterly.items()
        ],
        "monthly": monthly,
    }