import asyncio
import webbrowser
from threading import Timer

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from core.config import STATIC_DIR
from core.database import AsyncSessionLocal
from model import cart, notification_log, product, sales_record, user
from router import (
    auth_router,
    cart_router,
    notification_router,
    product_router,
    sales_record_router_dashboard,
    sales_record_router_detail,
    total_router,
    user_growth_router,
    user_loyal_router,
    user_router,
)
from service.notification_service import (
    create_cart_reminder_notifications,
    create_review_request_notifications,
)


app = FastAPI()


async def notification_worker():
    while True:
        # 장바구니 리마인드 알림 생성
        async with AsyncSessionLocal() as db:
            try:
                await create_cart_reminder_notifications(
                    db,
                    # 테스트용: 장바구니에 담은 지 1분 지나면 알림 대상
                    # 운영 시 after_minutes=60 으로 변경
                    after_minutes=1,

                    # 테스트용: 같은 장바구니 상태라도 1분마다 알림 이력 생성 가능
                    # 운영 시 repeat_minutes=1440 으로 변경하면 하루에 한 번만 재알림
                    repeat_minutes=1,
                )
                await db.commit()
            except Exception:
                await db.rollback()

        # 구매 감사 / 후기 독려 알림 생성
        async with AsyncSessionLocal() as db:
            try:
                # 테스트용: 구매 후 1일 지난 주문에 후기 팝업 알림 생성
                # 운영 시 배송 완료 예상 시점에 맞춰 after_days 값을 조정
                await create_review_request_notifications(db, after_days=1)
                await db.commit()
            except Exception:
                await db.rollback()

        # 테스트용: 30초마다 알림 생성 대상 확인
        # 운영 시 10분마다 확인하도록 60 * 10 으로 변경
        await asyncio.sleep(30)


@app.on_event("startup")
async def start_notification_worker():
    asyncio.create_task(notification_worker())


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=RedirectResponse)
async def index():
    return RedirectResponse("/product")


def open_browser():
    webbrowser.open("http://127.0.0.1:8000")


app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(product_router.router)
app.include_router(sales_record_router_detail.router)
app.include_router(sales_record_router_dashboard.router)
app.include_router(user_growth_router.router)
app.include_router(total_router.router)
app.include_router(user_loyal_router.router)
app.include_router(cart_router.router)
app.include_router(notification_router.router)


if __name__ == "__main__":
    Timer(1.5, open_browser).start()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_config=None,
    )