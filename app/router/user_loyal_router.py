from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse
from core.database import get_db
from core.config import templates
from service.user_loyal_service import get_customer_analysis_data

router = APIRouter(prefix="/admin/userloyal", tags=["admin userloyal"])

@router.get("/", response_class=HTMLResponse)
async def analysis_page(request: Request, db: AsyncSession = Depends(get_db)):
    data = await get_customer_analysis_data(db)
    return templates.TemplateResponse(request,
        "admin_userloyal.html", 
        {
            "ratios": data["ratios"],
            "preferences": data["preferences"]
        }
    )