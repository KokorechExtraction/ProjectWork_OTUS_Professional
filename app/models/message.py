import enum

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import IntIdPkMixin, TimestampMixin


class MessageStatus(enum.StrEnum):
    sent = "sent"
    delivered = "delivered"
    read = "read"


class Message(IntIdPkMixin, TimestampMixin, Base):
    __tablename__ = "messages"

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(default="")
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus, name="message_status"), default=MessageStatus.sent
    )

    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")
    reads = relationship("MessageRead", back_populates="message", cascade="all, delete-orphan")
    attachments = relationship(
        "MessageFile", back_populates="message", cascade="all, delete-orphan"
    )


class MessageRead(IntIdPkMixin, Base):
    __tablename__ = "message_reads"
    __table_args__ = (UniqueConstraint("message_id", "user_id", name="uq_message_read"),)

    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    message = relationship("Message", back_populates="reads")
    user = relationship("User")
