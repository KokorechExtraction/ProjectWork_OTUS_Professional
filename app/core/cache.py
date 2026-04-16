from app.core.redis import redis_runtime

USER_LIST_CACHE_TTL_SECONDS = 60
USER_WALL_CACHE_TTL_SECONDS = 60


def user_list_cache_key(current_user_id: int, query: str | None) -> str:
    normalized = (query or "").strip().lower() or "_all"
    return f"cache:users:list:{current_user_id}:{normalized}"


def user_wall_cache_key(viewer_id: int, user_id: int) -> str:
    return f"cache:posts:wall:{viewer_id}:{user_id}"


async def invalidate_user_list_cache() -> None:
    await redis_runtime.delete_pattern("cache:users:list:*")


async def invalidate_wall_cache_for_user(user_id: int) -> None:
    await redis_runtime.delete_pattern(f"cache:posts:wall:*:{user_id}")


async def invalidate_all_wall_caches() -> None:
    await redis_runtime.delete_pattern("cache:posts:wall:*")
