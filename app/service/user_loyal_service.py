from sqlalchemy import func, case, text, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from model.sales_record import SalesRecord
from model.product import Product

def get_user_stats_cte():
    """고객 유형 분류 로직을 담은 CTE 생성"""
    return (
        select(
            SalesRecord.user_id,
            func.count("*").label("total_count"),
            case(
                (
                    (func.now() - func.max(SalesRecord.sold_at) < text("INTERVAL '30 days'")) & 
                    (func.count("*") >= 10), 
                    '충성 고객'
                ),
                (func.count("*") == 1, '신규 고객'),
                else_='일반 고객'
            ).label("customer_type")
        )
        .group_by(SalesRecord.user_id)
        .cte("user_stats")
    )

async def calculate_customer_ratios(session: AsyncSession, user_stats_cte):
    """비동기 방식으로 고객 유형별 비중 및 명수 계산"""
    ratio_stmt = (
        select(
            user_stats_cte.c.customer_type,
            func.count("*").label("user_count")
        )
        .group_by(user_stats_cte.c.customer_type)
    )
    result = await session.execute(ratio_stmt)
    ratios_raw = result.all()
    
    total_users = sum(r.user_count for r in ratios_raw)
    return [
        {
            "type": r.customer_type,
            "user_count": r.user_count, # 명수 추가
            "percentage": round((r.user_count / total_users) * 100, 1) if total_users > 0 else 0
        } for r in ratios_raw
    ]

async def get_top_products_by_type(session: AsyncSession, user_stats_cte, customer_type: str):
    """비동기 방식으로 유형별 선호 상품 TOP 3 추출"""
    stmt = (
        select(Product.name, func.count(SalesRecord.id).label("sell_count"))
        .join(SalesRecord, SalesRecord.product_id == Product.id)
        .join(user_stats_cte, user_stats_cte.c.user_id == SalesRecord.user_id)
        .where(user_stats_cte.c.customer_type == customer_type)
        .group_by(Product.name)
        .order_by(desc("sell_count"))
        .limit(3)
    )
    result = await session.execute(stmt)
    results = result.all()
    return [{"name": r.name, "count": r.sell_count} for r in results]

async def get_customer_analysis_data(session: AsyncSession):
    """라우터 호출용 최종 데이터 조립 함수"""
    user_stats_cte = get_user_stats_cte()
    return {
        "ratios": await calculate_customer_ratios(session, user_stats_cte),
        "preferences": {
            "loyal": await get_top_products_by_type(session, user_stats_cte, '충성 고객'),
            "new": await get_top_products_by_type(session, user_stats_cte, '신규 고객'),
            "normal": await get_top_products_by_type(session, user_stats_cte, '일반 고객')
        }
    }