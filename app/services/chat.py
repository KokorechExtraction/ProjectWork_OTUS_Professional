from app.core.log_config import get_logger
from app.models.chat import Chat
from app.repositories.chat import ChatRepository
from app.repositories.user import UserRepository
from app.websocket.manager import manager

logger = get_logger(__name__)


class ChatService:
    def __init__(self, chat_repo: ChatRepository, user_repo: UserRepository) -> None:
        self.chat_repo = chat_repo
        self.user_repo = user_repo

    async def get_or_create_private_chat(self, current_user_id: int, other_user_id: int) -> Chat:
        if current_user_id == other_user_id:
            logger.warning("private_chat_failed_self_target", user_id=current_user_id)
            raise ValueError("Cannot create chat with yourself")
        if await self.user_repo.get_by_id(other_user_id) is None:
            logger.warning("private_chat_failed_user_not_found", target_user_id=other_user_id)
            raise ValueError("User not found")
        existing = await self.chat_repo.find_private_chat(current_user_id, other_user_id)
        if existing is not None:
            manager.register_chat_for_users(existing.id, [current_user_id, other_user_id])
            logger.info(
                "private_chat_reused",
                chat_id=existing.id,
                user_id=current_user_id,
                other_user_id=other_user_id,
            )
            return existing
        chat = await self.chat_repo.create_private_chat(current_user_id, other_user_id)
        manager.register_chat_for_users(chat.id, [current_user_id, other_user_id])
        logger.info(
            "private_chat_created",
            chat_id=chat.id,
            user_id=current_user_id,
            other_user_id=other_user_id,
        )
        return chat

    async def list_user_chats(self, user_id: int) -> list[Chat]:
        chats = await self.chat_repo.list_user_chats(user_id)
        logger.info("chat_list_loaded", user_id=user_id, count=len(chats))
        return chats
