from datetime import datetime

from pydantic import Field

from app.models.message import MessageStatus
from app.schemas.base import ORMBase
from app.schemas.file import FileOut
from app.schemas.user import UserBrief


class CreateMessageRequest(ORMBase):
    text: str = Field(default="", max_length=4000)
    file_ids: list[int] = Field(default_factory=list)


class UpdateMessageRequest(ORMBase):
    text: str = Field(min_length=1, max_length=4000)


class MessageOut(ORMBase):
    id: int
    chat_id: int
    sender_id: int
    sender: UserBrief | None = None
    text: str
    attachments: list[FileOut] = Field(default_factory=list)
    status: MessageStatus
    created_at: datetime
