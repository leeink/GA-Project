import uuid
from datetime import date

from pydantic import BaseModel, EmailStr, field_validator


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str
    gender: str | None = None
    birth_date: date | None = None
    address: str | None = None

    @field_validator("password")
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 characters long")
        return v

    @field_validator("nickname")
    def nickname_length(cls, v):
        if len(v) < 2 or len(v) > 8:
            raise ValueError("Nickname must be between 2 and 8 characters long")
        return v

    @field_validator("gender")
    def gender_options(cls, v):
        gender_map = {"남": "m", "여": "f", "m": "m", "f": "f"}
        if v is None:
            return v
        if v not in gender_map:
            raise ValueError("Gender must be 남 or 여")
        return gender_map[v]


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    nickname: str

    model_config = {"from_attributes": True}
