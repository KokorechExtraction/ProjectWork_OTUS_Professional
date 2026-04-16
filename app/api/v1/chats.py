from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.chat import ChatRepository
from app.repositories.user import UserRepository
from app.schemas.chat import ChatOut, CreatePrivateChatRequest
from app.services.chat import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/private", response_model=ChatOut)
async def create_private_chat(
    payload: CreatePrivateChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ChatOut:
    service = ChatService(ChatRepository(session), UserRepository(session))
    try:
        chat = await service.get_or_create_private_chat(current_user.id, payload.other_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChatOut.model_validate(chat)


@router.get("", response_model=list[ChatOut])
async def list_chats(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ChatOut]:
    chats = await ChatService(ChatRepository(session), UserRepository(session)).list_user_chats(
        current_user.id
    )
    return [ChatOut.model_validate(chat) for chat in chats]
