from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.chat import ChatService


@pytest.mark.asyncio
async def test_get_or_create_private_chat_rejects_unknown_user() -> None:
    chat_repo = AsyncMock()
    user_repo = AsyncMock()
    user_repo.get_by_id.return_value = None
    service = ChatService(chat_repo, user_repo)

    with pytest.raises(ValueError, match="User not found"):
        await service.get_or_create_private_chat(1, 2)


@pytest.mark.asyncio
async def test_get_or_create_private_chat_registers_chat_for_connected_users() -> None:
    chat = SimpleNamespace(id=15, created_at=datetime.now(UTC))
    chat_repo = AsyncMock()
    chat_repo.find_private_chat.return_value = None
    chat_repo.create_private_chat.return_value = chat
    user_repo = AsyncMock()
    user_repo.get_by_id.return_value = SimpleNamespace(id=2)
    service = ChatService(chat_repo, user_repo)

    with patch("app.services.chat.manager.register_chat_for_users") as register_chat:
        result = await service.get_or_create_private_chat(1, 2)

    assert result is chat
    chat_repo.create_private_chat.assert_awaited_once_with(1, 2)
    register_chat.assert_called_once_with(15, [1, 2])
