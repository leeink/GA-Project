from fastapi import APIRouter, Request
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from core.config import templates
from core.database import get_db
from service.sales_record_service_detail import *

router = APIRouter(prefix="/admin/detail", tags=["admin detail"])

@router.get("/{year}", response_class=HTMLResponse)
async def sales_record_detail(
    request: Request,
    year: str = "2026",
    db: AsyncSession = Depends(get_db),
):
    quarterly_rows = await find_quarterly_sales(db, year)
    monthly_rows   = await find_monthly_sales(db, year)
    product_rows   = await find_product_sales(db, year)
    yearly_total   = await find_yearly_total(db, year)

    # 분기 데이터 — 없는 분기는 0으로 채움
    quarterly_map = {int(q): int(s) for q, s in quarterly_rows}
    quarterly_data = [quarterly_map.get(q, 0) for q in range(1, 5)]

    # 월별 데이터 — 없는 월은 0으로 채움
    monthly_map = {int(m): int(s) for m, s in monthly_rows}
    monthly_data = [monthly_map.get(m, 0) for m in range(1, 13)]

    # 상품별 데이터
    product_labels = [r.product_name for r in product_rows]
    product_data   = [int(r.total_sales) for r in product_rows]

    return templates.TemplateResponse(
        request,
        "admin_detail.html",
        {
            "year":           year,
            "yearly_total":   yearly_total,
            "quarterly_data": quarterly_data,   # [q1, q2, q3, q4]
            "monthly_data":   monthly_data,     # [jan, ..., dec]
            "product_labels": product_labels,
            "product_data":   product_data,
        },
    )