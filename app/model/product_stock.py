import uuid, enum
from datetime import date

from sqlalchemy import Integer, Date, UUID, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

class Status(str, enum.Enum):
    NORMAL = "NORMAL"
    SOLDOUT = "SOLDOUT"
    EXPIRED = "EXPIRED"

class ProductStock(Base):
    __tablename__ = "product_stock"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product.id"))
    inbound_date: Mapped[date] = mapped_column(Date, default=date.today() ,nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, default=date.today(), nullable=False)
    init_quantity: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    current_quantity: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    status: Mapped[Status] = mapped_column(Enum(Status, name="status"), default=Status.NORMAL, nullable=False)