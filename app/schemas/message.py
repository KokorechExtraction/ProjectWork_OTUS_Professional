from datetime import datetime

from pydantic import Field

from app.models.message import MessageStatus
from app.schemas.base import ORMBase


class CreateMessageRequest(ORMBase):
    text: str = Field(default="", max_length=4000)
    file_ids: list[int] = Field(default_factory=list)


class MessageOut(ORMBase):
    id: int
    chat_id: int
    sender_id: int
    text: str
    status: MessageStatus
    created_at: datetime
