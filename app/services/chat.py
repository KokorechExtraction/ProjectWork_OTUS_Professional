from app.models.chat import Chat
from app.repositories.chat import ChatRepository
from app.repositories.user import UserRepository
from app.websocket.manager import manager


class ChatService:
    def __init__(self, chat_repo: ChatRepository, user_repo: UserRepository) -> None:
        self.chat_repo = chat_repo
        self.user_repo = user_repo

    async def get_or_create_private_chat(self, current_user_id: int, other_user_id: int) -> Chat:
        if current_user_id == other_user_id:
            raise ValueError("Cannot create chat with yourself")
        if await self.user_repo.get_by_id(other_user_id) is None:
            raise ValueError("User not found")
        existing = await self.chat_repo.find_private_chat(current_user_id, other_user_id)
        if existing is not None:
            manager.register_chat_for_users(existing.id, [current_user_id, other_user_id])
            return existing
        chat = await self.chat_repo.create_private_chat(current_user_id, other_user_id)
        manager.register_chat_for_users(chat.id, [current_user_id, other_user_id])
        return chat

    async def list_user_chats(self, user_id: int) -> list[Chat]:
        return await self.chat_repo.list_user_chats(user_id)
