from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse
from core.database import get_db
from core.config import templates
from core.security import get_current_user_from_cookie
from service.product_service import *
from schema.order_schema import OrderSchema 

router = APIRouter(prefix="/product", tags=["product"])

@router.get("/", response_class=HTMLResponse)
async def product_list(request: Request, db: AsyncSession = Depends(get_db)):
    products = await find_all_product(db)
    current_user = await get_current_user_from_cookie(request, db)
    
    last_address = ""
    if current_user:
        last_address = await get_last_address(db, current_user.id) or ""

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "products": products,
            "current_user": current_user,
            "last_address": last_address,
            "is_logged_in": True if current_user else False
        }
    )

@router.post('/order')
async def order(request: Request, dto: OrderSchema, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user: raise HTTPException(status_code=401)
    return await product_order(db, dto, current_user.id)