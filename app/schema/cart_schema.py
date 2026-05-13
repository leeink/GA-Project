import uuid
from pydantic import BaseModel, Field


class CartCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(ge=1)


class CartUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    cart_quantity: int
    product_name: str
    product_price: int
    stock: int = 0
