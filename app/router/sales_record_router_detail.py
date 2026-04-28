from fastapi import APIRouter, Request
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from core.config import templates
from core.database import get_db

router = APIRouter(prefix="/admin/detail", tags=["admin detail"])

@router.get("/{year}", response_class=HTMLResponse)
async def sales_record_detail(request: Request, db: AsyncSession = Depends(get_db), year: str = '2026'):
    return templates.TemplateResponse(
        request,
        "admin_detail.html",
        {
            "year": year,
        }
    )