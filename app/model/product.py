import enum
import uuid

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class CategoryType(str, enum.Enum):
    meal = "meal"
    snack = "snack"


class StorageType(str, enum.Enum):
    frozen = "frozen"
    fresh = "fresh"


class Product(Base):
    __tablename__ = "product"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category: Mapped[CategoryType] = mapped_column(Enum(CategoryType))
    storage_type: Mapped[StorageType] = mapped_column(Enum(StorageType))

    carts: Mapped[list["Cart"]] = relationship(back_populates="product")
    sales_records: Mapped[list["SalesRecord"]] = relationship(back_populates="product")
