from fastapi import APIRouter, Request
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from core.config import templates
from core.database import get_db
from service.sales_record_service_detail import *
# [추가 1] 예측 서비스 임포트
from service.prediction_service import PredictionService

router = APIRouter(prefix="/admin/detail", tags=["admin detail"])

@router.get("/{year}", response_class=HTMLResponse)
async def sales_record_detail(
    request: Request,
    year: str = "2026",
    db: AsyncSession = Depends(get_db),
):
    # --- 기존 코드 유지 ---
    available_years = await find_available_years(db)

    if not available_years:
        available_years = [int(year)]

    quarterly_rows = await find_quarterly_sales(db, year)
    monthly_rows   = await find_monthly_sales(db, year)
    product_rows   = await find_product_sales(db, year)
    yearly_total   = await find_yearly_total(db, year)

    quarterly_map  = {int(q): int(s) for q, s in quarterly_rows}
    quarterly_data = [quarterly_map.get(q, 0) for q in range(1, 5)]

    monthly_map  = {int(m): int(s) for m, s in monthly_rows}
    monthly_data = [monthly_map.get(m, 0) for m in range(1, 13)]

    product_labels = [r.product_name for r in product_rows]
    product_data   = [int(r.total_sales) for r in product_rows]
    # ----------------------

    # [수정 2] 동적 예측 데이터 처리
    # 드롭다운에서 받아온 문자열 year를 정수로 변환해서 서비스로 넘겨줘!
    target_year = int(year) 
    
    short_term_data = [0] * 12
    long_term_data = [0] * 12
    
    try:
        # 2026 고정 함수명에서 동적 함수명으로 변경 & target_year 인자 추가
        short_res = await PredictionService.predict_short_term(db, target_year)
        short_term_data = [item["sales"] for item in short_res]
        
        long_res = await PredictionService.predict_long_term(db, target_year)
        long_term_data = [item["sales"] for item in long_res]
    except Exception as e:
        print(f"Prediction Error: {e}") # 에러나면 터미널에 찍고 데이터는 0으로 넘김

    # [추가 3] return 딕셔너리에 데이터만 추가
    return templates.TemplateResponse(
        request,
        "admin_detail.html",
        {
            "year":            year,
            "available_years": available_years,
            "yearly_total":    yearly_total,
            "quarterly_data":  quarterly_data,
            "monthly_data":    monthly_data,
            "product_labels":  product_labels,
            "product_data":    product_data,
            # 여기 두 줄만 깔끔하게 추가!
            "short_term_data": short_term_data,
            "long_term_data":  long_term_data,
        },
    )