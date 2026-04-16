from datetime import datetime

from pydantic import Field

from app.schemas.base import ORMBase
from app.schemas.user import UserBrief


class CreatePostRequest(ORMBase):
    text: str = Field(min_length=1, max_length=2000)


class UpdatePostRequest(ORMBase):
    text: str = Field(min_length=1, max_length=2000)


class CreateCommentRequest(ORMBase):
    text: str = Field(min_length=1, max_length=1000)


class PostCommentOut(ORMBase):
    id: int
    post_id: int
    author_id: int
    author: UserBrief | None = None
    text: str
    created_at: datetime


class PostOut(ORMBase):
    id: int
    author_id: int
    author: UserBrief | None = None
    text: str
    created_at: datetime
    likes_count: int = 0
    liked_by_me: bool = False
    comments_count: int = 0
    comments: list[PostCommentOut] = Field(default_factory=list)
