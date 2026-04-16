from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import IntIdPkMixin, TimestampMixin


class User(IntIdPkMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    sent_messages = relationship("Message", back_populates="sender")
    files = relationship("File", back_populates="owner")
    posts = relationship("Post", back_populates="author")
