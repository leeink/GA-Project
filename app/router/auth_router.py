from types import SimpleNamespace
import uuid

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.params import Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse, RedirectResponse

from core.config import templates
from core.database import get_db
from core.security import get_current_user_from_cookie
from schema.auth_schema import TokenResponse, RefreshRequest, LogoutRequest
from schema.user_schema import UserResponse, UserCreateRequest
from service.auth_service import login, refresh_token, logout
from service.product_service import (
    delete_completed_order,
    find_completed_orders_by_user,
    update_completed_order_address,
    update_completed_order_quantity,
)
from service.user_service import create_user

router = APIRouter(prefix="/auth", tags=["auth"])


def render_auth_page(
        request: Request,
        mode: str,
        error: str | None = None,
        email: str = "",
        nickname: str = "",
        gender: str = "",
        birth_date: str = "",
        status_code: int = 200):
    return templates.TemplateResponse(
        request,
        "auth.html",
        {
            "mode": mode,
            "error": error,
            "email": email,
            "nickname": nickname,
            "gender": gender,
            "birth_date": birth_date,
        },
        status_code=status_code,
    )


@router.get("/register", response_class=HTMLResponse, summary="Register page")
async def register_page(request: Request):
    return render_auth_page(request, "register")


@router.post("/register/form", response_class=HTMLResponse, summary="Register from web form")
async def register_form(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        nickname: str = Form(...),
        gender: str = Form(...),
        birth_date: str = Form(...),
        db: AsyncSession = Depends(get_db)):
    try:
        data = UserCreateRequest(
            email=email,
            password=password,
            nickname=nickname,
            gender=gender,
            birth_date=birth_date,
        )
        await create_user(db, data)
    except ValidationError as exc:
        message = exc.errors()[0].get("msg", "입력값을 다시 확인해 주세요.")
        return render_auth_page(
            request,
            "register",
            message,
            email,
            nickname,
            gender,
            birth_date,
            status.HTTP_400_BAD_REQUEST,
        )
    except HTTPException as exc:
        message = "이미 가입된 이메일입니다." if exc.status_code == status.HTTP_409_CONFLICT else str(exc.detail)
        return render_auth_page(request, "register", message, email, nickname, gender, birth_date, exc.status_code)

    return RedirectResponse(url="/auth/login?registered=1", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse, summary="Login page")
async def login_page(request: Request, registered: bool = False):
    message = "회원가입이 완료되었습니다. 로그인해 주세요." if registered else None
    return render_auth_page(request, "login", message)


@router.get("/mypage", response_class=HTMLResponse, summary="My page")
async def mypage(
        request: Request,
        db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_from_cookie(request, db)
    if current_user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    completed_orders = await find_completed_orders_by_user(db, current_user.id)
    latest_order_address = completed_orders[0]["address"] if completed_orders else None

    return templates.TemplateResponse(
        request,
        "mypage.html",
        {
            "current_user": current_user,
            "completed_orders": completed_orders,
            "latest_order_address": latest_order_address,
        },
    )


@router.post("/admin/check", summary="Check admin and redirect")
async def check_admin(request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_from_cookie(request, db)
    if current_user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    if not current_user.is_admin:
        return RedirectResponse(url="/product/", status_code=status.HTTP_303_SEE_OTHER)

    return RedirectResponse(url="/admin/detail/2026", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/mypage/order/{order_id}/edit", summary="Edit completed order quantity")
async def edit_completed_order(
        order_id: uuid.UUID,
        request: Request,
        quantity: int = Form(...),
        db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_from_cookie(request, db)
    if current_user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    await update_completed_order_quantity(db, current_user.id, order_id, quantity)
    return RedirectResponse(url="/auth/mypage", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/mypage/address/edit", summary="Edit completed order address")
async def edit_completed_order_address(
        request: Request,
        address: str = Form(...),
        db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_from_cookie(request, db)
    if current_user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    await update_completed_order_address(db, current_user.id, address)
    return RedirectResponse(url="/auth/mypage", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/mypage/order/{order_id}/delete", summary="Delete completed order")
async def remove_completed_order(
        order_id: uuid.UUID,
        request: Request,
        db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_from_cookie(request, db)
    if current_user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    await delete_completed_order(db, current_user.id, order_id)
    return RedirectResponse(url="/auth/mypage", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/login/form", response_class=HTMLResponse, summary="Login from web form")
async def login_form(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: AsyncSession = Depends(get_db)):
    try:
        tokens = await login(db, SimpleNamespace(username=email, password=password))
    except HTTPException as exc:
        return render_auth_page(
            request,
            "login",
            "이메일 또는 비밀번호를 확인해 주세요.",
            email=email,
            status_code=exc.status_code,
        )

    response = RedirectResponse(url="/product/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("access_token", tokens.access_token, httponly=True, samesite="lax")
    response.set_cookie("refresh_token", tokens.refresh_token, httponly=True, samesite="lax")
    return response


@router.post("/logout/form", summary="Logout from web")
async def logout_form(request: Request, db: AsyncSession = Depends(get_db)):
    refresh_token_value = request.cookies.get("refresh_token")
    if refresh_token_value:
        await logout(db, refresh_token_value)

    response = RedirectResponse(url="/product/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

@router.post("/register",
             response_model=UserResponse,
             status_code=201, summary="Register a new user")
async def register(data: UserCreateRequest, db: AsyncSession = Depends(get_db)):
    return await create_user(db, data)

@router.post("/login",
             response_model=TokenResponse,
             summary="Login and get access token")
async def login_route(
        data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)):
    return await login(db, data)

@router.post("/refresh",
             response_model=TokenResponse,
             summary="Refresh access token")
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_token(db, data.refresh_token)

@router.post("/logout", status_code=204, summary="logout")
async def logout_route(data: LogoutRequest, db: AsyncSession = Depends(get_db)):
    return await logout(db, data.refresh_token)
