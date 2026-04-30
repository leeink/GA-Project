from fastapi import APIRouter, Request
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from core.database import get_db
from core.config import templates
from core.security import get_current_user_from_cookie
from service.product_service import *

router = APIRouter(prefix="/product",tags=["product"])


async def render_product_index(
        request: Request,
        db: AsyncSession,
        products,
        **context):
    current_user = await get_current_user_from_cookie(request, db)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "products": products,
            "current_user": current_user,
            **context,
        },
    )

@router.get("/", response_class=HTMLResponse)
async def product_list(request: Request, db: AsyncSession = Depends(get_db)):
    products = await find_all_product(db)
    return await render_product_index(request, db, products)


# 상품명 검색
@router.get("/search", response_class=HTMLResponse)
async def product_search(request: Request, name: str = "", db: AsyncSession = Depends(get_db)):
    products = await find_product_search(db, name) if name else await find_all_product(db)
    return await render_product_index(request, db, products, search=name)


# 카테고리 필터
@router.get("/category", response_class=HTMLResponse)
async def product_by_category(request: Request, category: str = "", db: AsyncSession = Depends(get_db)):
    products = await find_product_by_category(db, category) if category else await find_all_product(db)
    return await render_product_index(request, db, products, category=category)

@router.post('/order')
async def order(request: Request, dto: OrderSchema, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_from_cookie(request, db)
    user_id = current_user.id if current_user else None
    return await product_order(db, dto, user_id=user_id)
