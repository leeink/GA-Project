import uuid

from fastapi import APIRouter, Request
from fastapi.params import Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from core.database import get_db
from core.exceptions import NotFoundException
from core.security import get_current_user
from core.config import templates
from schema.user_schema import UserResponse, UserCreateRequest
from service.user_service import find_user_by_id, find_all_user, create_user

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/",
            response_model=list[UserResponse],
            summary="Get all users")
async def get_users(db: AsyncSession = Depends(get_db)):
    return await find_all_user(db)

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return current_user


@router.get("/{user_id}",
            response_model=UserResponse,
            summary="Get user by id")
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    user = await find_user_by_id(db, user_id)
    if not user:
        raise NotFoundException("User not found")
    return user

@router.post("/create",
             status_code=201,
             summary="Create a new user")
async def create_user_route(data:UserCreateRequest, db: AsyncSession = Depends(get_db)):
    await create_user(db, data)