from datetime import datetime

from pydantic import Field

from app.schemas.base import ORMBase


class CreatePostRequest(ORMBase):
    text: str = Field(min_length=1, max_length=2000)


class PostOut(ORMBase):
    id: int
    author_id: int
    text: str
    created_at: datetime
    likes_count: int = 0
    liked_by_me: bool = False
