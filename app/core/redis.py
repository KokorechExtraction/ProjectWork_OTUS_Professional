import json

from collections.abc import AsyncIterator
from contextlib import suppress

from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from app.core.config import settings
from app.core.log_config import get_logger

logger = get_logger(__name__)


class RedisRuntime:
    def __init__(self) -> None:
        self._client: Redis | None = None

    @property
    def client(self) -> Redis | None:
        return self._client

    @property
    def is_available(self) -> bool:
        return self._client is not None

    async def connect(self) -> None:
        if self._client is not None:
            return
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        try:
            await client.ping()
        except Exception as exc:
            await client.aclose()
            logger.warning("redis_unavailable", redis_url=settings.redis_url, detail=str(exc))
            return
        self._client = client
        logger.info("redis_connected", redis_url=settings.redis_url)

    async def disconnect(self) -> None:
        if self._client is None:
            return
        await self._client.aclose()
        self._client = None
        logger.info("redis_disconnected")

    async def publish_json(self, channel: str, payload: dict) -> bool:
        if self._client is None:
            return False
        await self._client.publish(channel, json.dumps(payload))
        return True

    async def get_json(self, key: str):
        if self._client is None:
            return None
        raw = await self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, value, ttl_seconds: int) -> bool:
        if self._client is None:
            return False
        await self._client.set(key, json.dumps(value), ex=ttl_seconds)
        return True

    async def delete_pattern(self, pattern: str) -> int:
        if self._client is None:
            return 0
        deleted = 0
        async for key in self._scan_iter(pattern):
            deleted += await self._client.delete(key)
        return deleted

    async def subscribe(self, channel: str) -> PubSub | None:
        if self._client is None:
            return None
        pubsub = self._client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    async def unsubscribe(self, pubsub: PubSub | None, channel: str) -> None:
        if pubsub is None:
            return
        with suppress(Exception):
            await pubsub.unsubscribe(channel)
        with suppress(Exception):
            await pubsub.aclose()

    async def _scan_iter(self, pattern: str) -> AsyncIterator[str]:
        if self._client is None:
            return
        cursor = 0
        while True:
            cursor, keys = await self._client.scan(cursor=cursor, match=pattern, count=100)
            for key in keys:
                yield key
            if cursor == 0:
                break


redis_runtime = RedisRuntime()
