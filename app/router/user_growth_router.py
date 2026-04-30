from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.config import templates
from service.user_growth_service import find_yearly_user_growth, find_quarterly_compare_data, find_monthly_compare_data, find_total_user_count
from starlette.responses import HTMLResponse

#대쉬보드 접속루트
router = APIRouter(prefix="/admin/usergrowth", tags=["admin usergrowth"])

#대쉬보드 초기
@router.get("/{year}", response_class=HTMLResponse)
async def get_dashboard_page(request: Request, year: str):
    return templates.TemplateResponse(request, "admin_usergrowth.html",{ "year": year})

@router.get("/api/total-count")
async def get_total_count(db: AsyncSession = Depends(get_db)):
    count = await find_total_user_count(db)
    return {"total_count": count}

@router.get("/api/yearly/{year}")
async def get_yearly_api(year: str, db: AsyncSession = Depends(get_db)):
    return {"data": await find_yearly_user_growth(db, year)}

@router.get("/api/quarterly/{year}")
async def get_quarterly_api(year: str, db: AsyncSession = Depends(get_db)):
    return {"data": await find_quarterly_compare_data(db, year)}

@router.get("/api/monthly/{year}")
async def get_monthly_api(year: str, db: AsyncSession = Depends(get_db)):
    return {"data": await find_monthly_compare_data(db, year)}
