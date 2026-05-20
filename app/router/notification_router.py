import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user_from_cookie
from schema.notification_schema import NotificationResponse
from service.notification_service import (
    get_unread_notifications,
    mark_notification_read,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


async def require_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return current_user


@router.get("/unread", response_model=list[NotificationResponse])
async def unread_notifications(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    return await get_unread_notifications(db, current_user.id)


@router.patch("/{notification_id}/read")
async def read_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    notification = await mark_notification_read(db, current_user.id, notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")

    return {"ok": True}
