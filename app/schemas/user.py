from pydantic import EmailStr

from app.schemas.base import IdSchema, TimestampSchema


class UserOut(IdSchema, TimestampSchema):
    username: str
    email: EmailStr
