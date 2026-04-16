from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatParticipant
from app.models.file import File, MessageFile
from app.models.message import Message


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, owner_id: int, original_name: str, stored_name: str, content_type: str, size: int, path: str) -> File:
        file = File(owner_id=owner_id, original_name=original_name, stored_name=stored_name, content_type=content_type, size=size, path=path)
        self.session.add(file)
        await self.session.commit()
        await self.session.refresh(file)
        return file

    async def get_by_id(self, file_id: int) -> File | None:
        result = await self.session.execute(select(File).where(File.id == file_id))
        return result.scalar_one_or_none()

    async def list_by_ids_owned_by_user(self, file_ids: list[int], owner_id: int) -> list[File]:
        if not file_ids:
            return []
        result = await self.session.execute(
            select(File).where(and_(File.id.in_(file_ids), File.owner_id == owner_id))
        )
        return list(result.scalars().all())

    async def get_accessible_by_user(self, file_id: int, user_id: int) -> File | None:
        result = await self.session.execute(
            select(File)
            .outerjoin(MessageFile, MessageFile.file_id == File.id)
            .outerjoin(Message, Message.id == MessageFile.message_id)
            .outerjoin(ChatParticipant, ChatParticipant.chat_id == Message.chat_id)
            .where(
                File.id == file_id,
                (File.owner_id == user_id) | (ChatParticipant.user_id == user_id),
            )
            .distinct()
        )
        return result.scalar_one_or_none()
