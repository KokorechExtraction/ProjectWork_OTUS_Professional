from pydantic import EmailStr, Field

from app.schemas.base import IdSchema, ORMBase, TimestampSchema


class UserBrief(IdSchema):
    username: str
    email: EmailStr
    is_admin: bool
    is_active: bool


class UserOut(UserBrief, TimestampSchema):
    pass


class UpdateUserRequest(ORMBase):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
