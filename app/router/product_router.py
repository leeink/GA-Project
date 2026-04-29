from fastapi import APIRouter, Form, Request
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse, RedirectResponse

from core.database import get_db
from core.config import templates
from service.product_service import *

router = APIRouter(prefix="/product",tags=["product"])

@router.get("/", response_class=HTMLResponse)
async def product_list(request: Request, db: AsyncSession = Depends(get_db)):
    products = await find_all_product(db)
    return templates.TemplateResponse(request, "index.html", {"products": products})


# 상품명 검색
@router.get("/search", response_class=HTMLResponse)
async def product_search(request: Request, name: str = "", db: AsyncSession = Depends(get_db)):
    products = await find_product_search(db, name) if name else await find_all_product(db)
    return templates.TemplateResponse(request, "index.html", {"products": products, "search": name})


# 카테고리 필터
@router.get("/category", response_class=HTMLResponse)
async def product_by_category(request: Request, category: str = "", db: AsyncSession = Depends(get_db)):
    products = await find_product_by_category(db, category) if category else await find_all_product(db)
    return templates.TemplateResponse(request, "index.html", {"products": products, "category": category})

@router.post('/order')
async def order(dto: OrderSchema, db: AsyncSession = Depends(get_db)):
    await product_order(db, dto)

    return RedirectResponse(url="/product", status_code=303)