from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schema.auth_schema import TokenResponse, LoginRequest, RefreshRequest, LogoutRequest
from app.schema.user_schema import UserResponse, UserCreateRequest
from app.service.auth_service import login, refresh_token, logout
from app.service.user_service import create_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register",
             response_model=UserResponse,
             status_code=201, summary="Register a new user")
async def register(data: UserCreateRequest, db: AsyncSession = Depends(get_db)):
    return await create_user(db, data)

@router.post("/login",
             response_model=TokenResponse,
             summary="Login and get access token")
async def login_route(
        data: LoginRequest,
        db: AsyncSession = Depends(get_db)):
    return await login(db, data)

@router.post("/refresh",
             response_model=TokenResponse,
             summary="Refresh access token")
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_token(db, data.refresh_token)

@router.post("/logout", status_code=204, summary="logout")
async def logout_route(data: LogoutRequest, db: AsyncSession = Depends(get_db)):
    return logout(db, data.refresh_token)