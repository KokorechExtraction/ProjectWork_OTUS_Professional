from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_user
from app.core.security import create_access_token
from app.db.session import get_db_session
from app.main import app


class DummySession:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return None


def _override_user():
    return SimpleNamespace(
        id=1, username="tester", email="tester@example.com", is_admin=False, is_active=True
    )


async def _override_session():
    yield object()


def test_users_list_returns_cached_payload_without_hitting_repository() -> None:
    cached_user = {
        "id": 2,
        "username": "vasya",
        "email": "vasya@example.com",
        "is_admin": False,
        "is_active": True,
        "created_at": "2026-04-16T10:00:00Z",
        "updated_at": "2026-04-16T10:00:00Z",
    }
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db_session] = _override_session

    try:
        with (
            patch("app.main.AsyncSessionLocal", return_value=DummySession()),
            patch("app.main.ensure_admin_user", new_callable=AsyncMock),
            patch("app.api.v1.users.redis_runtime.get_json", new_callable=AsyncMock) as get_json,
            patch("app.api.v1.users.UserRepository.list_all", new_callable=AsyncMock) as list_all,
            patch("app.api.v1.users.UserRepository.search", new_callable=AsyncMock) as search,
            TestClient(app) as client,
        ):
            get_json.return_value = [cached_user]

            response = client.get("/api/v1/users", headers={"Authorization": "Bearer test"})

        assert response.status_code == 200
        assert response.json()[0]["username"] == "vasya"
        list_all.assert_not_awaited()
        search.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_users_list_cache_miss_loads_repository_and_populates_cache() -> None:
    user = SimpleNamespace(
        id=3,
        username="petya",
        email="petya@example.com",
        is_admin=False,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_db_session] = _override_session

    try:
        with (
            patch("app.main.AsyncSessionLocal", return_value=DummySession()),
            patch("app.main.ensure_admin_user", new_callable=AsyncMock),
            patch("app.api.v1.users.redis_runtime.get_json", new_callable=AsyncMock) as get_json,
            patch("app.api.v1.users.redis_runtime.set_json", new_callable=AsyncMock) as set_json,
            patch("app.api.v1.users.UserRepository.search", new_callable=AsyncMock) as search,
            TestClient(app) as client,
        ):
            get_json.return_value = None
            search.return_value = [user]

            response = client.get(
                "/api/v1/users",
                params={"q": "petya"},
                headers={"Authorization": "Bearer test"},
            )

        assert response.status_code == 200
        assert response.json()[0]["email"] == "petya@example.com"
        search.assert_awaited_once()
        set_json.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()


def test_websocket_endpoint_connects_and_acknowledges_messages() -> None:
    token = create_access_token(user=SimpleNamespace(id=7, username="ws-user", is_admin=False))[
        "access_token"
    ]

    with (
        patch("app.main.AsyncSessionLocal", return_value=DummySession()),
        patch("app.main.ensure_admin_user", new_callable=AsyncMock),
        patch("app.api.v1.websocket.AsyncSessionLocal", return_value=DummySession()),
        patch(
            "app.api.v1.websocket.ChatRepository.list_user_chats", new_callable=AsyncMock
        ) as list_user_chats,
        TestClient(app) as client,
    ):
        list_user_chats.return_value = [SimpleNamespace(id=10)]

        with client.websocket_connect(f"/api/v1/ws?token={token}") as websocket:
            websocket.send_json({"ping": "pong"})
            payload = websocket.receive_json()

    assert payload == {"type": "ack", "data": {"ping": "pong"}}
