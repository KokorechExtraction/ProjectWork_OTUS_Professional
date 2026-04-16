from datetime import datetime

from pydantic import Field

from app.schemas.base import ORMBase


class CreatePrivateChatRequest(ORMBase):
    other_user_id: int = Field(gt=0)


class ChatOut(ORMBase):
    id: int
    created_at: datetime
