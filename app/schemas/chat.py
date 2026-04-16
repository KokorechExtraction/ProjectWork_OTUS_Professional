from datetime import datetime

from pydantic import Field

from app.schemas.base import ORMBase
from app.schemas.user import UserBrief


class CreatePrivateChatRequest(ORMBase):
    other_user_id: int = Field(gt=0)


class ChatOut(ORMBase):
    id: int
    created_at: datetime
    other_user: UserBrief | None = None


class AdminChatOut(ORMBase):
    id: int
    created_at: datetime
    participants: list[UserBrief] = Field(default_factory=list)
