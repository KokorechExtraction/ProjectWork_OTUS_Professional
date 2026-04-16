from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.chat import ChatRepository
from app.repositories.user import UserRepository
from app.schemas.chat import ChatOut, CreatePrivateChatRequest
from app.schemas.mappers import to_chat_out, to_chat_out_list
from app.services.chat import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/private", response_model=ChatOut)
async def create_private_chat(
    payload: CreatePrivateChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ChatOut:
    chat_repo = ChatRepository(session)
    user_repo = UserRepository(session)
    service = ChatService(chat_repo, user_repo)
    try:
        chat = await service.get_or_create_private_chat(current_user.id, payload.other_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await to_chat_out(chat, current_user.id, user_repo, chat_repo)


@router.get("", response_model=list[ChatOut])
async def list_chats(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ChatOut]:
    chat_repo = ChatRepository(session)
    user_repo = UserRepository(session)
    chats = await ChatService(chat_repo, user_repo).list_user_chats(current_user.id)
    return await to_chat_out_list(chats, current_user.id, user_repo, chat_repo)
