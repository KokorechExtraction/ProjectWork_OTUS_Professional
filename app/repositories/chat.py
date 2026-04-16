from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat, ChatParticipant


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_private_chat(self, user_a: int, user_b: int) -> Chat:
        chat = Chat()
        self.session.add(chat)
        await self.session.flush()
        self.session.add_all(
            [
                ChatParticipant(chat_id=chat.id, user_id=user_a),
                ChatParticipant(chat_id=chat.id, user_id=user_b),
            ]
        )
        await self.session.commit()
        await self.session.refresh(chat)
        return chat

    async def find_private_chat(self, user_a: int, user_b: int) -> Chat | None:
        subq = (
            select(ChatParticipant.chat_id)
            .where(ChatParticipant.user_id.in_([user_a, user_b]))
            .group_by(ChatParticipant.chat_id)
            .having(func.count(ChatParticipant.user_id) == 2)
        )
        result = await self.session.execute(select(Chat).where(Chat.id.in_(subq)))
        return result.scalar_one_or_none()

    async def list_user_chats(self, user_id: int) -> list[Chat]:
        result = await self.session.execute(
            select(Chat)
            .join(ChatParticipant, ChatParticipant.chat_id == Chat.id)
            .where(ChatParticipant.user_id == user_id)
            .order_by(Chat.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all_chats(self) -> list[Chat]:
        result = await self.session.execute(select(Chat).order_by(Chat.created_at.desc()))
        return list(result.scalars().all())

    async def list_participant_ids(self, chat_id: int) -> list[int]:
        result = await self.session.execute(
            select(ChatParticipant.user_id).where(ChatParticipant.chat_id == chat_id)
        )
        return list(result.scalars().all())

    async def is_user_in_chat(self, chat_id: int, user_id: int) -> bool:
        result = await self.session.execute(
            select(ChatParticipant).where(
                and_(ChatParticipant.chat_id == chat_id, ChatParticipant.user_id == user_id)
            )
        )
        return result.scalar_one_or_none() is not None
