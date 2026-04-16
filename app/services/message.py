from app.models.message import Message
from app.repositories.chat import ChatRepository
from app.repositories.file import FileRepository
from app.repositories.message import MessageRepository
from app.websocket.manager import manager


class MessageService:
    def __init__(
        self,
        chat_repo: ChatRepository,
        message_repo: MessageRepository,
        file_repo: FileRepository,
    ) -> None:
        self.chat_repo = chat_repo
        self.message_repo = message_repo
        self.file_repo = file_repo

    async def send_message(self, current_user_id: int, chat_id: int, text: str, file_ids: list[int]) -> Message:
        allowed = await self.chat_repo.is_user_in_chat(chat_id, current_user_id)
        if not allowed:
            raise ValueError("User is not participant of chat")
        normalized_text = text.strip()
        if not normalized_text and not file_ids:
            raise ValueError("Message must contain text or attachments")
        owned_files = await self.file_repo.list_by_ids_owned_by_user(file_ids, current_user_id)
        if len(owned_files) != len(set(file_ids)):
            raise ValueError("One or more attached files are unavailable")
        message = await self.message_repo.create(
            chat_id=chat_id,
            sender_id=current_user_id,
            text=normalized_text,
        )
        if file_ids:
            await self.message_repo.attach_files(message.id, file_ids)
        await manager.broadcast_to_chat(
            chat_id,
            {
                "type": "message:new",
                "data": {
                    "chat_id": chat_id,
                    "message_id": message.id,
                    "sender_id": current_user_id,
                    "text": normalized_text,
                    "file_ids": file_ids,
                },
            },
        )
        return message

    async def list_chat_messages(self, current_user_id: int, chat_id: int) -> list[Message]:
        allowed = await self.chat_repo.is_user_in_chat(chat_id, current_user_id)
        if not allowed:
            raise ValueError("User is not participant of chat")
        return await self.message_repo.list_chat_messages(chat_id)

    async def mark_read(self, current_user_id: int, message_id: int) -> Message:
        message = await self.message_repo.get_by_id(message_id)
        if message is None:
            raise ValueError("Message not found")
        allowed = await self.chat_repo.is_user_in_chat(message.chat_id, current_user_id)
        if not allowed:
            raise ValueError("User is not participant of chat")
        message = await self.message_repo.mark_read(message, current_user_id)
        await manager.broadcast_to_chat(
            message.chat_id,
            {
                "type": "message:read",
                "data": {"message_id": message.id, "user_id": current_user_id},
            },
        )
        return message
