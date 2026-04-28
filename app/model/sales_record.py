import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from product import Product


class SalesRecord(Base):
    __tablename__ = "sales_record"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sold_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("siteuser.id"))
    quantity: Mapped[int] = mapped_column()
    sales_price: Mapped[int] = mapped_column()

    product: Mapped["Product"] = relationship(back_populates="sales_records")