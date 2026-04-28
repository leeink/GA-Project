from fastapi import APIRouter, Form, Request
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from core.database import get_db
from core.config import templates
from service.product_service import find_all_product, find_product_by_name

router = APIRouter(prefix="/product",tags=["product"])