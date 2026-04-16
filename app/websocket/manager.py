from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, list[WebSocket]] = defaultdict(list)
        self.user_chats: dict[int, set[int]] = defaultdict(set)

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
        for user_id, chats in self.user_chats.items():
            if chat_id in chats:
                await self.send_to_user(user_id, payload)


manager = ConnectionManager()
