import asyncio
import json

from collections import defaultdict
from contextlib import suppress

from fastapi import WebSocket

from app.core.log_config import get_logger
from app.core.redis import redis_runtime

logger = get_logger(__name__)
REDIS_CHAT_CHANNEL = "chat_events"


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, list[WebSocket]] = defaultdict(list)
        self.user_chats: dict[int, set[int]] = defaultdict(set)
        self._listener_task: asyncio.Task | None = None

    async def start(self) -> None:
        if not redis_runtime.is_available or self._listener_task is not None:
            return
        self._listener_task = asyncio.create_task(self._listen_for_chat_events())
        logger.info("websocket_redis_listener_started", channel=REDIS_CHAT_CHANNEL)

    async def stop(self) -> None:
        if self._listener_task is None:
            return
        self._listener_task.cancel()
        with suppress(asyncio.CancelledError):
            await self._listener_task
        self._listener_task = None
        logger.info("websocket_redis_listener_stopped", channel=REDIS_CHAT_CHANNEL)

    async def connect(self, user_id: int, websocket: WebSocket, chat_ids: list[int]) -> None:
        await websocket.accept()
        self.active_connections[user_id].append(websocket)
        self.user_chats[user_id] = set(chat_ids)

    def register_chat_for_users(self, chat_id: int, user_ids: list[int]) -> None:
        for user_id in user_ids:
            self.user_chats[user_id].add(chat_id)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        if websocket in self.active_connections.get(user_id, []):
            self.active_connections[user_id].remove(websocket)
        if not self.active_connections.get(user_id):
            self.active_connections.pop(user_id, None)
            self.user_chats.pop(user_id, None)

    async def send_to_user(self, user_id: int, payload: dict) -> None:
        for ws in self.active_connections.get(user_id, []):
            await ws.send_json(payload)

    async def broadcast_to_chat(self, chat_id: int, payload: dict) -> None:
        if await redis_runtime.publish_json(
            REDIS_CHAT_CHANNEL, {"chat_id": chat_id, "payload": payload}
        ):
            return
        await self._dispatch_to_chat(chat_id, payload)

    async def _dispatch_to_chat(self, chat_id: int, payload: dict) -> None:
        for user_id, chats in self.user_chats.items():
            if chat_id in chats:
                await self.send_to_user(user_id, payload)

    async def _listen_for_chat_events(self) -> None:
        pubsub = await redis_runtime.subscribe(REDIS_CHAT_CHANNEL)
        if pubsub is None:
            return
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is None:
                    await asyncio.sleep(0.05)
                    continue
                try:
                    event = json.loads(message["data"])
                    await self._dispatch_to_chat(int(event["chat_id"]), event["payload"])
                except Exception as exc:
                    logger.warning("websocket_redis_event_invalid", detail=str(exc))
        finally:
            await redis_runtime.unsubscribe(pubsub, REDIS_CHAT_CHANNEL)


manager = ConnectionManager()
