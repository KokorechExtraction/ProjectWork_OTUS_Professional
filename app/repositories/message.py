from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import MessageFile
from app.models.message import Message, MessageRead, MessageStatus


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, chat_id: int, sender_id: int, text: str) -> Message:
        message = Message(chat_id=chat_id, sender_id=sender_id, text=text, status=MessageStatus.sent)
        self.session.add(message)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def attach_files(self, message_id: int, file_ids: list[int]) -> None:
        for file_id in file_ids:
            self.session.add(MessageFile(message_id=message_id, file_id=file_id))
        await self.session.commit()

    async def list_chat_messages(self, chat_id: int) -> list[Message]:
        result = await self.session.execute(select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc()))
        return list(result.scalars().all())

    async def get_by_id(self, message_id: int) -> Message | None:
        result = await self.session.execute(select(Message).where(Message.id == message_id))
        return result.scalar_one_or_none()

    async def mark_delivered(self, message: Message) -> Message:
        message.status = MessageStatus.delivered
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def mark_read(self, message: Message, user_id: int) -> Message:
        result = await self.session.execute(select(MessageRead).where(and_(MessageRead.message_id == message.id, MessageRead.user_id == user_id)))
        existing = result.scalar_one_or_none()
        if existing is None:
            self.session.add(MessageRead(message_id=message.id, user_id=user_id, read_at=datetime.now(UTC)))
        message.status = MessageStatus.read
        await self.session.commit()
        await self.session.refresh(message)
        return message
