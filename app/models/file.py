from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import IntIdPkMixin, TimestampMixin


class File(IntIdPkMixin, TimestampMixin, Base):
    __tablename__ = "files"

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str] = mapped_column(String(255))
    size: Mapped[int]
    path: Mapped[str] = mapped_column(String(500))

    owner = relationship("User", back_populates="files")
    message_links = relationship("MessageFile", back_populates="file", cascade="all, delete-orphan")


class MessageFile(IntIdPkMixin, Base):
    __tablename__ = "message_files"

    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"))

    message = relationship("Message", back_populates="attachments")
    file = relationship("File", back_populates="message_links")
