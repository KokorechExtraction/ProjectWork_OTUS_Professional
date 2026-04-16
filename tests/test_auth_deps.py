from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_admin, get_current_user
from app.models.user import User

DUMMY_SESSION = cast(AsyncSession, object())


@pytest.mark.asyncio
async def test_get_current_user_requires_bearer_token() -> None:
    with pytest.raises(HTTPException, match="Missing bearer token") as exc_info:
        await get_current_user(DUMMY_SESSION, None)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_token() -> None:
    with (
        patch("app.api.deps.auth.decode_access_token", side_effect=ValueError("Invalid token")),
        pytest.raises(HTTPException, match="Invalid token") as exc_info,
    ):
        await get_current_user(DUMMY_SESSION, "Bearer bad-token")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_user() -> None:
    with (
        patch("app.api.deps.auth.decode_access_token", return_value={"sub": "5"}),
        patch("app.api.deps.auth.UserRepository") as repo_cls,
        pytest.raises(HTTPException, match="User not found") as exc_info,
    ):
        repo_cls.return_value.get_by_id = AsyncMock(return_value=None)
        await get_current_user(DUMMY_SESSION, "Bearer valid-token")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_inactive_user() -> None:
    user = SimpleNamespace(id=5, is_active=False)
    with (
        patch("app.api.deps.auth.decode_access_token", return_value={"sub": "5"}),
        patch("app.api.deps.auth.UserRepository") as repo_cls,
        pytest.raises(HTTPException, match="User is inactive") as exc_info,
    ):
        repo_cls.return_value.get_by_id = AsyncMock(return_value=user)
        await get_current_user(DUMMY_SESSION, "Bearer valid-token")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_admin_rejects_non_admin_user() -> None:
    with pytest.raises(HTTPException, match="Admin access required") as exc_info:
        await get_current_admin(cast(User, SimpleNamespace(is_admin=False)))

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_admin_returns_admin_user() -> None:
    admin = cast(User, SimpleNamespace(is_admin=True, id=1))

    result = await get_current_admin(admin)

    assert result is admin
