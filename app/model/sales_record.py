import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, DateTime, UUID, Integer, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class SalesRecord(Base):
    __tablename__ = "sales_record"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sold_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("siteuser.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    sales_price: Mapped[int] = mapped_column(Integer, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="sales_records")