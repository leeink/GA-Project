from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.config import templates
from service.sales_record_service_dashboard import selectYear_totalSales, best5_count, best5_sales
from starlette.responses import HTMLResponse

# === [26.05.04] xlsx파일 저장 ===
from fastapi.responses import StreamingResponse
from service.excel_download_service import get_raw_db_excel
from datetime import datetime

#대쉬보드 접속루트
router = APIRouter(prefix="/admin/dashboard", tags=["admin dashboard"])

#대쉬보드 초기
@router.get("/", response_class=HTMLResponse)
async def get_dashboard_page(request: Request):
    return templates.TemplateResponse(request, "admin_dashboard.html")

#연도별 총매출
@router.get("/yearlySales")
async def yearlySales(db: AsyncSession = Depends(get_db)):
    sql = await selectYear_totalSales(db)
    return {"data": sql}

#많이 팔린 상품 TOP 5 (판매량 기준)
@router.get("/best5_count")
async def get_best5_count(db: AsyncSession = Depends(get_db)):
    sql = await best5_count(db)
    return {"data": sql}

#매출 순위 상품 TOP 5 (총액 기준)
@router.get("/best5_sales")
async def get_best5_sales(db: AsyncSession = Depends(get_db)):
    sql = await best5_sales(db)
    return {"data": sql}

#연도별 매출[타사비교] 비교 예정

# === [26.05.04] xlsx파일 저장 ===
@router.get("/excel_download")
async def download_custom_report(
    s_year: int, e_year: int, s_month: int, e_month: int,
    db: AsyncSession = Depends(get_db)
):
    # 서비스 호출하여 모든 테이블 데이터가 담긴 엑셀 생성
    excel_file = await get_raw_db_excel(db)
    
    filename = f"Business_Raw_Data_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )