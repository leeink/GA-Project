from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from model.cart import Cart
from model.notification_log import NotificationLog
from model.product import Product
from model.sales_record import SalesRecord
from model.user import User


async def already_created(
    db: AsyncSession,
    user_id: uuid.UUID,
    kind: str,
    reference_id: str,
) -> bool:
    result = await db.execute(
        select(NotificationLog).where(
            NotificationLog.user_id == user_id,
            NotificationLog.kind == kind,
            NotificationLog.reference_id == reference_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def create_popup_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    kind: str,
    reference_id: str,
    message: str,
):
    if await already_created(db, user_id, kind, reference_id):
        return

    db.add(
        NotificationLog(
            user_id=user_id,
            kind=kind,
            reference_id=reference_id,
            message=message,
        )
    )


async def create_cart_reminder_notifications(
    db: AsyncSession,
    after_minutes: int = 60,
    repeat_minutes: int = 1440,
):
    standard_time = datetime.now(timezone.utc) - timedelta(minutes=after_minutes)

    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.product))
        .where(Cart.current_time.is_not(None))
        .where(Cart.current_time <= standard_time)
    )

    cart_items = result.scalars().all()

    user_cart_map = {}

    for item in cart_items:
        user_cart_map.setdefault(item.user_id, []).append(item)

    for user_id, items in user_cart_map.items():
        user = await db.get(User, user_id)
        if not user:
            continue

        last_cart_time = max(item.current_time for item in items)
        first_product_name = items[0].product.name if items[0].product else "장바구니 상품"
        cart_count = len(items)

        reference_prefix = f"cart:{user.id}:{last_cart_time.isoformat()}"

        if await recently_created(
            db=db,
            user_id=user.id,
            kind="cart_reminder",
            reference_prefix=reference_prefix,
            within_minutes=repeat_minutes,
        ):
            continue

        created_at = datetime.now(timezone.utc).isoformat()
        reference_id = f"{reference_prefix}:notice:{created_at}"

        message = (
            f"{user.nickname}님, 고민 중이신 상품이 있어요!\n\n"
            f"대표 상품: {first_product_name}\n"
            f"장바구니 상품 수: {cart_count}개\n\n"
            "담아두신 상품을 지금 확인해보세요."
        )

        db.add(
            NotificationLog(
                user_id=user.id,
                kind="cart_reminder",
                reference_id=reference_id,
                message=message,
            )
        )




async def create_review_request_notifications(
    db: AsyncSession,
    after_days: int = 2,
):
    기준시간 = datetime.now(timezone.utc) - timedelta(days=after_days)

    result = await db.execute(
        select(SalesRecord)
        .options(selectinload(SalesRecord.product))
        .where(SalesRecord.sold_at <= 기준시간)
    )

    sales_records = result.scalars().all()

    for record in sales_records:
        if not record.user_id:
            continue

        user = await db.get(User, record.user_id)
        if not user:
            continue

        product_name = record.product.name if record.product else "구매하신 상품"
        reference_id = f"sales_record:{record.id}"

        message = (
            f"{user.nickname}님, 구매해주셔서 감사합니다.\n\n"
            f"{product_name} 상품은 잘 받아보셨나요?\n"
            "후기를 작성해주시면 포인트 안내를 도와드릴게요."
        )

        await create_popup_notification(
            db=db,
            user_id=user.id,
            kind="review_request",
            reference_id=reference_id,
            message=message,
        )


async def get_unread_notifications(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(
        select(NotificationLog)
        .where(
            NotificationLog.user_id == user_id,
            NotificationLog.read_at.is_(None),
        )
        .order_by(NotificationLog.sent_at.asc())
    )
    return result.scalars().all()


async def mark_notification_read(
    db: AsyncSession,
    user_id: uuid.UUID,
    notification_id: uuid.UUID,
):
    result = await db.execute(
        select(NotificationLog).where(
            NotificationLog.id == notification_id,
            NotificationLog.user_id == user_id,
        )
    )
    notification = result.scalar_one_or_none()

    if notification:
        notification.read_at = datetime.now(timezone.utc)

    await db.flush()
    return notification


async def recently_created(
    db: AsyncSession,
    user_id: uuid.UUID,
    kind: str,
    reference_prefix: str,
    within_minutes: int,
) -> bool:
    기준시간 = datetime.now(timezone.utc) - timedelta(minutes=within_minutes)

    result = await db.execute(
        select(NotificationLog).where(
            NotificationLog.user_id == user_id,
            NotificationLog.kind == kind,
            NotificationLog.reference_id.like(f"{reference_prefix}%"),
            NotificationLog.sent_at >= 기준시간,
        )
    )

    return result.scalar_one_or_none() is not None