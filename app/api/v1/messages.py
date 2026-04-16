from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.chat import ChatRepository
from app.repositories.file import FileRepository
from app.repositories.message import MessageRepository
from app.repositories.user import UserRepository
from app.schemas.mappers import to_message_out, to_message_out_list
from app.schemas.message import CreateMessageRequest, MessageOut, UpdateMessageRequest
from app.services.message import MessageService

router = APIRouter(tags=["messages"])


@router.post("/chats/{chat_id}/messages", response_model=MessageOut)
async def create_message(
    chat_id: int,
    payload: CreateMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MessageOut:
    chat_repo = ChatRepository(session)
    message_repo = MessageRepository(session)
    file_repo = FileRepository(session)
    service = MessageService(chat_repo, message_repo, file_repo)
    try:
        message = await service.send_message(
            current_user.id,
            chat_id,
            payload.text,
            payload.file_ids,
            is_admin=current_user.is_admin,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_message_out(message, current_user)


@router.get("/chats/{chat_id}/messages", response_model=list[MessageOut])
async def list_messages(
    chat_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[MessageOut]:
    chat_repo = ChatRepository(session)
    message_repo = MessageRepository(session)
    file_repo = FileRepository(session)
    user_repo = UserRepository(session)
    service = MessageService(chat_repo, message_repo, file_repo)
    try:
        messages = await service.list_chat_messages(
            current_user.id, chat_id, is_admin=current_user.is_admin
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    sender_ids = {message.sender_id for message in messages}
    sender_map: dict[int, User] = {}
    for sender_id in sender_ids:
        sender = await user_repo.get_by_id(sender_id)
        if sender is not None:
            sender_map[sender_id] = sender
    return to_message_out_list(messages, sender_map)


@router.post("/messages/{message_id}/read", response_model=MessageOut)
async def mark_message_read(
    message_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MessageOut:
    chat_repo = ChatRepository(session)
    message_repo = MessageRepository(session)
    file_repo = FileRepository(session)
    service = MessageService(chat_repo, message_repo, file_repo)
    try:
        message = await service.mark_read(current_user.id, message_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_message_out(message, current_user if message.sender_id == current_user.id else None)


@router.patch("/messages/{message_id}", response_model=MessageOut)
async def edit_message(
    message_id: int,
    payload: UpdateMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MessageOut:
    chat_repo = ChatRepository(session)
    message_repo = MessageRepository(session)
    file_repo = FileRepository(session)
    user_repo = UserRepository(session)
    service = MessageService(chat_repo, message_repo, file_repo)
    try:
        message = await service.edit_message(
            current_user.id,
            message_id,
            payload.text,
            is_admin=current_user.is_admin,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    sender = await user_repo.get_by_id(message.sender_id)
    return to_message_out(message, sender)


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    chat_repo = ChatRepository(session)
    message_repo = MessageRepository(session)
    file_repo = FileRepository(session)
    service = MessageService(chat_repo, message_repo, file_repo)
    try:
        await service.delete_message(current_user.id, message_id, is_admin=current_user.is_admin)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
