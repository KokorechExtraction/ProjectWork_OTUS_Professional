from app.core.log_config import get_logger
from app.models.message import Message
from app.repositories.chat import ChatRepository
from app.repositories.file import FileRepository
from app.repositories.message import MessageRepository
from app.websocket.manager import manager

logger = get_logger(__name__)


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

    async def send_message(
        self,
        current_user_id: int,
        chat_id: int,
        text: str,
        file_ids: list[int],
        *,
        is_admin: bool = False,
    ) -> Message:
        allowed = is_admin or await self.chat_repo.is_user_in_chat(chat_id, current_user_id)
        if not allowed:
            logger.warning("message_send_forbidden", user_id=current_user_id, chat_id=chat_id)
            raise ValueError("User is not participant of chat")
        normalized_text = text.strip()
        if not normalized_text and not file_ids:
            logger.warning("message_send_empty", user_id=current_user_id, chat_id=chat_id)
            raise ValueError("Message must contain text or attachments")
        owned_files = await self.file_repo.list_by_ids_owned_by_user(file_ids, current_user_id)
        if len(owned_files) != len(set(file_ids)):
            logger.warning(
                "message_send_invalid_attachments",
                user_id=current_user_id,
                chat_id=chat_id,
                file_ids=file_ids,
            )
            raise ValueError("One or more attached files are unavailable")
        message = await self.message_repo.create(
            chat_id=chat_id,
            sender_id=current_user_id,
            text=normalized_text,
        )
        if file_ids:
            await self.message_repo.attach_files(message.id, file_ids)
        message = await self.message_repo.get_by_id(message.id) or message
        await manager.broadcast_to_chat(
            chat_id,
            {
                "type": "message:new",
                "data": {
                    "chat_id": chat_id,
                    "message_id": message.id,
                    "sender_id": current_user_id,
                    "sender_username": None,
                    "text": normalized_text,
                    "attachments": [
                        {
                            "id": attachment.file.id,
                            "original_name": attachment.file.original_name,
                            "content_type": attachment.file.content_type,
                            "size": attachment.file.size,
                        }
                        for attachment in getattr(message, "attachments", [])
                        if getattr(attachment, "file", None) is not None
                    ],
                },
            },
        )
        logger.info(
            "message_sent",
            message_id=message.id,
            chat_id=chat_id,
            sender_id=current_user_id,
            attachment_count=len(file_ids),
            has_text=bool(normalized_text),
        )
        return message

    async def list_chat_messages(
        self, current_user_id: int, chat_id: int, *, is_admin: bool = False
    ) -> list[Message]:
        allowed = is_admin or await self.chat_repo.is_user_in_chat(chat_id, current_user_id)
        if not allowed:
            logger.warning("message_list_forbidden", user_id=current_user_id, chat_id=chat_id)
            raise ValueError("User is not participant of chat")
        messages = await self.message_repo.list_chat_messages(chat_id)
        logger.info(
            "message_list_loaded", user_id=current_user_id, chat_id=chat_id, count=len(messages)
        )
        return messages

    async def edit_message(
        self, current_user_id: int, message_id: int, text: str, *, is_admin: bool = False
    ) -> Message:
        message = await self.message_repo.get_by_id(message_id)
        if message is None:
            logger.warning("message_edit_not_found", user_id=current_user_id, message_id=message_id)
            raise ValueError("Message not found")
        if not is_admin and message.sender_id != current_user_id:
            logger.warning(
                "message_edit_forbidden",
                user_id=current_user_id,
                message_id=message_id,
                chat_id=message.chat_id,
            )
            raise ValueError("User cannot edit this message")
        normalized_text = text.strip()
        if not normalized_text:
            logger.warning(
                "message_edit_empty",
                user_id=current_user_id,
                message_id=message_id,
                chat_id=message.chat_id,
            )
            raise ValueError("Message text cannot be empty")
        message = await self.message_repo.update_text(message, normalized_text)
        await manager.broadcast_to_chat(
            message.chat_id,
            {
                "type": "message:updated",
                "data": {
                    "chat_id": message.chat_id,
                    "message_id": message.id,
                    "sender_id": message.sender_id,
                    "sender_username": None,
                    "text": message.text,
                },
            },
        )
        logger.info(
            "message_edited",
            message_id=message.id,
            chat_id=message.chat_id,
            editor_id=current_user_id,
            is_admin=is_admin,
        )
        return message

    async def mark_read(self, current_user_id: int, message_id: int) -> Message:
        message = await self.message_repo.get_by_id(message_id)
        if message is None:
            logger.warning("message_read_not_found", user_id=current_user_id, message_id=message_id)
            raise ValueError("Message not found")
        allowed = await self.chat_repo.is_user_in_chat(message.chat_id, current_user_id)
        if not allowed:
            logger.warning(
                "message_read_forbidden",
                user_id=current_user_id,
                message_id=message_id,
                chat_id=message.chat_id,
            )
            raise ValueError("User is not participant of chat")
        message = await self.message_repo.mark_read(message, current_user_id)
        await manager.broadcast_to_chat(
            message.chat_id,
            {
                "type": "message:read",
                "data": {"message_id": message.id, "user_id": current_user_id},
            },
        )
        logger.info(
            "message_read", message_id=message.id, user_id=current_user_id, chat_id=message.chat_id
        )
        return message

    async def delete_message(
        self, current_user_id: int, message_id: int, *, is_admin: bool = False
    ) -> None:
        message = await self.message_repo.get_by_id(message_id)
        if message is None:
            logger.warning(
                "message_delete_not_found", user_id=current_user_id, message_id=message_id
            )
            raise ValueError("Message not found")
        if not is_admin and message.sender_id != current_user_id:
            logger.warning(
                "message_delete_forbidden",
                user_id=current_user_id,
                message_id=message_id,
                chat_id=message.chat_id,
            )
            raise ValueError("User cannot delete this message")
        chat_id = message.chat_id
        deleted_message_id = message.id
        await self.message_repo.delete_message(message)
        await manager.broadcast_to_chat(
            chat_id,
            {
                "type": "message:deleted",
                "data": {"chat_id": chat_id, "message_id": deleted_message_id},
            },
        )
        logger.info(
            "message_deleted",
            message_id=deleted_message_id,
            chat_id=chat_id,
            deleter_id=current_user_id,
            is_admin=is_admin,
        )
