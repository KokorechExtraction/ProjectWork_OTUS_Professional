from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.models.message import MessageStatus
from app.services.message import MessageService


@pytest.mark.asyncio
async def test_send_message_requires_text_or_attachments() -> None:
    chat_repo = AsyncMock()
    chat_repo.is_user_in_chat.return_value = True
    service = MessageService(chat_repo, AsyncMock(), AsyncMock())

    with pytest.raises(ValueError, match="text or attachments"):
        await service.send_message(1, 10, "   ", [])


@pytest.mark.asyncio
async def test_send_message_rejects_files_not_owned_by_user() -> None:
    chat_repo = AsyncMock()
    chat_repo.is_user_in_chat.return_value = True
    file_repo = AsyncMock()
    file_repo.list_by_ids_owned_by_user.return_value = [SimpleNamespace(id=10)]
    service = MessageService(chat_repo, AsyncMock(), file_repo)

    with pytest.raises(ValueError, match="attached files"):
        await service.send_message(1, 10, "hello", [10, 11])


@pytest.mark.asyncio
async def test_send_message_normalizes_text_and_broadcasts() -> None:
    message = SimpleNamespace(
        id=55,
        chat_id=10,
        sender_id=1,
        text="hello",
        status=MessageStatus.sent,
        created_at=datetime.now(UTC),
    )
    chat_repo = AsyncMock()
    chat_repo.is_user_in_chat.return_value = True
    message_repo = AsyncMock()
    message_repo.create.return_value = message
    message_repo.get_by_id.return_value = message
    file_repo = AsyncMock()
    file_repo.list_by_ids_owned_by_user.return_value = [SimpleNamespace(id=7)]
    service = MessageService(chat_repo, message_repo, file_repo)

    with patch(
        "app.services.message.manager.broadcast_to_chat", new_callable=AsyncMock
    ) as broadcast:
        result = await service.send_message(1, 10, "  hello  ", [7])

    assert result is message
    message_repo.create.assert_awaited_once_with(chat_id=10, sender_id=1, text="hello")
    message_repo.attach_files.assert_awaited_once_with(55, [7])
    broadcast.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_message_allows_admin_for_foreign_chat() -> None:
    message = SimpleNamespace(
        id=77,
        chat_id=10,
        sender_id=999,
        text="admin here",
        status=MessageStatus.sent,
        created_at=datetime.now(UTC),
    )
    chat_repo = AsyncMock()
    chat_repo.is_user_in_chat.return_value = False
    message_repo = AsyncMock()
    message_repo.create.return_value = message
    message_repo.get_by_id.return_value = message
    file_repo = AsyncMock()
    file_repo.list_by_ids_owned_by_user.return_value = []
    service = MessageService(chat_repo, message_repo, file_repo)

    with patch("app.services.message.manager.broadcast_to_chat", new_callable=AsyncMock):
        result = await service.send_message(999, 10, "admin here", [], is_admin=True)

    assert result is message
    message_repo.create.assert_awaited_once_with(chat_id=10, sender_id=999, text="admin here")
    chat_repo.is_user_in_chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_edit_message_allows_admin() -> None:
    message = SimpleNamespace(
        id=55,
        chat_id=10,
        sender_id=1,
        text="hello",
        status=MessageStatus.sent,
        created_at=datetime.now(UTC),
    )
    chat_repo = AsyncMock()
    message_repo = AsyncMock()
    message_repo.get_by_id.return_value = message
    message_repo.update_text.return_value = message
    file_repo = AsyncMock()
    service = MessageService(chat_repo, message_repo, file_repo)

    with patch(
        "app.services.message.manager.broadcast_to_chat", new_callable=AsyncMock
    ) as broadcast:
        result = await service.edit_message(999, 55, "  fixed  ", is_admin=True)

    assert result is message
    message_repo.update_text.assert_awaited_once_with(message, "fixed")
    broadcast.assert_awaited_once()
