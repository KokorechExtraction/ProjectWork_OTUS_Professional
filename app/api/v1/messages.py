from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.chat import ChatRepository
from app.repositories.file import FileRepository
from app.repositories.message import MessageRepository
from app.schemas.message import CreateMessageRequest, MessageOut
from app.services.message import MessageService

router = APIRouter(tags=["messages"])


@router.post("/chats/{chat_id}/messages", response_model=MessageOut)
async def create_message(
    chat_id: int,
    payload: CreateMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MessageOut:
    service = MessageService(ChatRepository(session), MessageRepository(session), FileRepository(session))
    try:
        message = await service.send_message(current_user.id, chat_id, payload.text, payload.file_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MessageOut.model_validate(message)


@router.get("/chats/{chat_id}/messages", response_model=list[MessageOut])
async def list_messages(
    chat_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[MessageOut]:
    service = MessageService(ChatRepository(session), MessageRepository(session), FileRepository(session))
    try:
        messages = await service.list_chat_messages(current_user.id, chat_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [MessageOut.model_validate(message) for message in messages]


@router.post("/messages/{message_id}/read", response_model=MessageOut)
async def mark_message_read(
    message_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MessageOut:
    service = MessageService(ChatRepository(session), MessageRepository(session), FileRepository(session))
    try:
        message = await service.mark_read(current_user.id, message_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MessageOut.model_validate(message)
