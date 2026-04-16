from unittest.mock import AsyncMock

import pytest

from sqlalchemy.exc import IntegrityError

from app.services.auth import AuthService


@pytest.mark.asyncio
async def test_register_rejects_duplicate_username() -> None:
    repo = AsyncMock()
    repo.get_by_username.return_value = object()
    repo.get_by_email.return_value = None

    service = AuthService(repo)

    with pytest.raises(ValueError, match="Username already taken"):
        await service.register("taken", "user@example.com", "Test1234")


@pytest.mark.asyncio
async def test_register_rolls_back_on_integrity_error() -> None:
    repo = AsyncMock()
    repo.get_by_username.return_value = None
    repo.get_by_email.return_value = None
    repo.create.side_effect = IntegrityError("stmt", {}, Exception("duplicate"))

    service = AuthService(repo)

    with pytest.raises(ValueError, match="Username or email already exists"):
        await service.register("user", "user@example.com", "Test1234")

    repo.session.rollback.assert_awaited_once()
