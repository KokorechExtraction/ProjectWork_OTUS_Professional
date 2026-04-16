from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_admin
from app.core.cache import invalidate_all_wall_caches, invalidate_user_list_cache
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.chat import ChatRepository
from app.repositories.post import PostRepository
from app.repositories.user import UserRepository
from app.schemas.chat import AdminChatOut
from app.schemas.mappers import to_admin_chat_out_list, to_user_out
from app.schemas.user import UserOut
from app.services.admin import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
async def admin_list_users(
    _: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[UserOut]:
    users = await AdminService(
        UserRepository(session), PostRepository(session), ChatRepository(session)
    ).list_users()
    return [to_user_out(user) for user in users]


@router.get("/users/{user_id}/chats", response_model=list[AdminChatOut])
async def admin_list_user_chats(
    user_id: int,
    _: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AdminChatOut]:
    user_repo = UserRepository(session)
    chat_repo = ChatRepository(session)
    try:
        chats = await AdminService(user_repo, PostRepository(session), chat_repo).list_user_chats(
            user_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await to_admin_chat_out_list(chats, user_repo, chat_repo)


@router.post("/users/{user_id}/ban", response_model=UserOut)
async def admin_ban_user(
    user_id: int,
    admin_user: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserOut:
    try:
        user = await AdminService(
            UserRepository(session), PostRepository(session), ChatRepository(session)
        ).ban_user(admin_user, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await invalidate_user_list_cache()
    await invalidate_all_wall_caches()
    return to_user_out(user)


@router.post("/users/{user_id}/unban", response_model=UserOut)
async def admin_unban_user(
    user_id: int,
    admin_user: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserOut:
    try:
        user = await AdminService(
            UserRepository(session), PostRepository(session), ChatRepository(session)
        ).unban_user(admin_user, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await invalidate_user_list_cache()
    await invalidate_all_wall_caches()
    return to_user_out(user)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_post(
    post_id: int,
    admin_user: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    try:
        await AdminService(
            UserRepository(session), PostRepository(session), ChatRepository(session)
        ).delete_post(admin_user, post_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
