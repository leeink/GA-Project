import uuid

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.user import User
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.core.security import get_current_user
from app.schema.user_schema import UserResponse, UserCreateRequest
from app.service.user_service import find_user_by_id, find_all_user, create_user

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/",
            response_model=list[UserResponse],
            summary="Get all users")
async def get_users(db: AsyncSession = Depends(get_db)):
    return await find_all_user(db)

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
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