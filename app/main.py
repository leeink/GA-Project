from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from core.config import STATIC_DIR
from router import auth_router, user_router, product_router, sales_record_router_detail, sales_record_router_dashboard, user_growth_router, total_router
from router import user_loyal_router
from model import user, product, cart, sales_record

app = FastAPI()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(product_router.router)
app.include_router(sales_record_router_detail.router)
app.include_router(sales_record_router_dashboard.router) #dashboard 라우터 추가
app.include_router(user_growth_router.router) #usergrowth 라우터 추가
app.include_router(total_router.router)
app.include_router(user_loyal_router.router) #userloyal 라우터 추가
