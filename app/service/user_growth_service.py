# [SERVICE] 유저 성장률 비교 데이터 조회 (전년 vs 당해)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, extract, func
from model.user import User

# 전체 고객수(2015~2025)
async def find_total_user_count(db: AsyncSession):
    query = select(func.count(User.id))
    result = await db.execute(query)
    return result.scalar() or 0

# 년간 비교
async def find_yearly_user_growth(db: AsyncSession, year: str):
    curr_year = int(year)
    prev_year = curr_year - 1
    query = select(
        extract("year", User.created_at).label("year"),
        func.count(User.id).label("user_count")
    ).where(extract("year", User.created_at).in_([curr_year, prev_year])
    ).group_by(extract("year", User.created_at))
    
    result = await db.execute(query)
    data = {row.year: row.user_count for row in result.all()}
    curr_count = data.get(curr_year, 0)
    prev_count = data.get(prev_year, 0)
    growth_rate = ((curr_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
    
    return {
        "current_count": curr_count,
        "previous_count": prev_count,
        "growth_rate": round(growth_rate, 2)
    }

# 분기별 비교
async def find_quarterly_compare_data(db: AsyncSession, year: str):
    """분기별 비교 데이터 (전년/당해)"""
    curr_year = int(year)
    prev_year = curr_year - 1
    query = select(
        extract("year", User.created_at).label("year"),
        extract("quarter", User.created_at).label("quarter"),
        func.count(User.id).label("count")
    ).where(extract("year", User.created_at).in_([curr_year, prev_year])
    ).group_by("year", "quarter")
    
    result = await db.execute(query)
    stats = {prev_year: {}, curr_year: {}}
    for row in result.all():
        stats[row.year][row.quarter] = row.count

    return [
        {
            "quarter": q,
            "prev_count": stats[prev_year].get(q, 0),
            "curr_count": stats[curr_year].get(q, 0)
        } for q in range(1, 5)
    ]

# 월간 비교
async def find_monthly_compare_data(db: AsyncSession, year: str):
    """월별 비교 데이터 (전년/당해)"""
    curr_year = int(year)
    prev_year = curr_year - 1
    query = select(
        extract("year", User.created_at).label("year"),
        extract("month", User.created_at).label("month"),
        func.count(User.id).label("count")
    ).where(extract("year", User.created_at).in_([curr_year, prev_year])
    ).group_by("year", "month")
    
    result = await db.execute(query)
    stats = {prev_year: {}, curr_year: {}}
    for row in result.all():
        stats[row.year][row.month] = row.count

    return [
        {
            "month": m,
            "prev_count": stats[prev_year].get(m, 0),
            "curr_count": stats[curr_year].get(m, 0)
        } for m in range(1, 13)
    ]