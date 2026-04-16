from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.mappers import to_user_out
from app.schemas.user import UserOut
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(
    payload: RegisterRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> UserOut:
    service = AuthService(UserRepository(session))
    try:
        user = await service.register(payload.username, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_user_out(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> TokenResponse:
    service = AuthService(UserRepository(session))
    try:
        token = await service.login(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenResponse(**token)


@router.get("/me", response_model=UserOut)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return to_user_out(current_user)
