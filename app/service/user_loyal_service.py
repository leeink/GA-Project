import asyncio

from sqlalchemy import func, case, text, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from model.product import Product
from model.sales_record import SalesRecord


def get_user_stats_cte():
    return (
        select(
            SalesRecord.user_id,
            func.count().label("total_count"),          # count("*") → count()
            func.max(SalesRecord.sold_at).label("last_purchased_at"),
            case(
                (
                    (func.now() - func.max(SalesRecord.sold_at) < text("INTERVAL '30 days'")) &
                    (func.count() >= 10),
                    "충성 고객"
                ),
                else_="일반 고객"
            ).label("customer_type")
        )
        .group_by(SalesRecord.user_id)
        .cte("user_stats")
    )


async def get_customer_analysis_data(session: AsyncSession):
    """
    3번 왕복 → 1번으로 통합
    비율 계산 + TOP5 두 유형을 단일 쿼리로 처리
    """
    user_stats_cte = get_user_stats_cte()
    sell_count = func.count(SalesRecord.id).label("sell_count")

    # ── 비율 쿼리 ──────────────────────────────
    ratio_stmt = (
        select(
            user_stats_cte.c.customer_type,
            func.count().label("user_count")
        )
        .group_by(user_stats_cte.c.customer_type)
    )

    # ── TOP5 쿼리 (충성/일반 한 번에) ──────────
    # customer_type을 같이 SELECT해서 Python에서 분리
    top_products_stmt = (
        select(
            user_stats_cte.c.customer_type,
            Product.name,
            sell_count,
            func.rank().over(
                partition_by=user_stats_cte.c.customer_type,
                order_by=desc(func.count(SalesRecord.id))
            ).label("rnk")
        )
        .join(SalesRecord, SalesRecord.product_id == Product.id)
        .join(user_stats_cte, user_stats_cte.c.user_id == SalesRecord.user_id)
        .group_by(user_stats_cte.c.customer_type, Product.name)
    )
    top_products_subq = top_products_stmt.subquery()

    top_final_stmt = (
        select(top_products_subq)
        .where(top_products_subq.c.rnk <= 5)
        .order_by(top_products_subq.c.customer_type, top_products_subq.c.rnk)
    )

    ratio_result = await session.execute(ratio_stmt)
    top_result = await session.execute(top_final_stmt)

    # ── 비율 조립 ──────────────────────────────
    ratios_raw = ratio_result.all()
    total_users = sum(r.user_count for r in ratios_raw)
    results_dict = {r.customer_type: r.user_count for r in ratios_raw}
    target_types = ["충성 고객", "일반 고객"]

    ratios = [
        {
            "type": t,
            "user_count": results_dict.get(t, 0),
            "percentage": round(results_dict.get(t, 0) / total_users * 100, 1) if total_users > 0 else 0,
        }
        for t in target_types
    ]

    # ── TOP5 조립 ──────────────────────────────
    preferences: dict[str, list] = {"충성 고객": [], "일반 고객": []}
    for row in top_result.all():
        preferences[row.customer_type].append(
            {"name": row.name, "count": row.sell_count}
        )

    return {
        "ratios": ratios,
        "preferences": {
            "loyal":  preferences["충성 고객"],
            "normal": preferences["일반 고객"],
        },
    }