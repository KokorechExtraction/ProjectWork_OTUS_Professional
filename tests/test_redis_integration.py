from unittest.mock import AsyncMock, PropertyMock, call, patch

import pytest

from app.core.cache import (
    invalidate_all_wall_caches,
    invalidate_user_list_cache,
    invalidate_wall_cache_for_user,
    user_list_cache_key,
    user_wall_cache_key,
)
from app.websocket.manager import ConnectionManager


@pytest.mark.asyncio
async def test_broadcast_to_chat_uses_redis_pubsub_when_available() -> None:
    manager = ConnectionManager()

    with (
        patch(
            "app.websocket.manager.redis_runtime.publish_json", new_callable=AsyncMock
        ) as publish,
        patch.object(manager, "_dispatch_to_chat", new_callable=AsyncMock) as dispatch,
    ):
        publish.return_value = True

        await manager.broadcast_to_chat(10, {"type": "message:new"})

    publish.assert_awaited_once_with(
        "chat_events", {"chat_id": 10, "payload": {"type": "message:new"}}
    )
    dispatch.assert_not_awaited()


@pytest.mark.asyncio
async def test_broadcast_to_chat_falls_back_to_local_dispatch_without_redis() -> None:
    manager = ConnectionManager()

    with (
        patch(
            "app.websocket.manager.redis_runtime.publish_json", new_callable=AsyncMock
        ) as publish,
        patch.object(manager, "_dispatch_to_chat", new_callable=AsyncMock) as dispatch,
    ):
        publish.return_value = False

        await manager.broadcast_to_chat(22, {"type": "message:updated"})

    dispatch.assert_awaited_once_with(22, {"type": "message:updated"})


@pytest.mark.asyncio
async def test_manager_start_skips_listener_when_redis_unavailable() -> None:
    manager = ConnectionManager()

    with (
        patch(
            "app.core.redis.RedisRuntime.is_available", new_callable=PropertyMock
        ) as is_available,
        patch("app.websocket.manager.asyncio.create_task") as create_task,
    ):
        is_available.return_value = False
        await manager.start()

    create_task.assert_not_called()
    assert manager._listener_task is None


def test_cache_key_builders_normalize_values() -> None:
    assert user_list_cache_key(5, None) == "cache:users:list:5:_all"
    assert user_list_cache_key(5, "  Vasya ") == "cache:users:list:5:vasya"
    assert user_wall_cache_key(3, 9) == "cache:posts:wall:3:9"


@pytest.mark.asyncio
async def test_cache_invalidation_uses_expected_patterns() -> None:
    with patch(
        "app.core.cache.redis_runtime.delete_pattern", new_callable=AsyncMock
    ) as delete_pattern:
        await invalidate_user_list_cache()
        await invalidate_wall_cache_for_user(7)
        await invalidate_all_wall_caches()

    assert delete_pattern.await_args_list == [
        call("cache:users:list:*"),
        call("cache:posts:wall:*:7"),
        call("cache:posts:wall:*"),
    ]
