from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.log_config import get_logger
from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.repositories.chat import ChatRepository
from app.websocket.manager import manager

router = APIRouter(tags=["websocket"])
logger = get_logger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)) -> None:
    payload = decode_access_token(token)
    user_id = int(payload["sub"])

    async with AsyncSessionLocal() as session:
        chats = await ChatRepository(session).list_user_chats(user_id)
        chat_ids = [chat.id for chat in chats]

    await manager.connect(user_id, websocket, chat_ids)
    logger.info("websocket_connected", user_id=user_id, chat_count=len(chat_ids))
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"type": "ack", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
        logger.info("websocket_disconnected", user_id=user_id)
