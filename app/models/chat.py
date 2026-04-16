from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import IntIdPkMixin, TimestampMixin


class Chat(IntIdPkMixin, TimestampMixin, Base):
    __tablename__ = "chats"

    participants = relationship(
        "ChatParticipant", back_populates="chat", cascade="all, delete-orphan"
    )
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class ChatParticipant(IntIdPkMixin, TimestampMixin, Base):
    __tablename__ = "chat_participants"
    __table_args__ = (UniqueConstraint("chat_id", "user_id", name="uq_chat_participant"),)

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    chat = relationship("Chat", back_populates="participants")
    user = relationship("User")
