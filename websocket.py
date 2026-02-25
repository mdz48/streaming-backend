from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)

    async def broadcast(self, message: dict, sender_id: str = None):
        disconnected = []
        for uid, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(uid)
        for uid in disconnected:
            self.disconnect(uid)

    async def send_to(self, user_id: str, message: dict):
        connection = self.active_connections.get(user_id)
        if connection:
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/chat/{user_id}")
async def chat_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    await manager.broadcast({
        "type": "system",
        "message": f"{user_id} se ha unido al chat.",
        "sender": "system"
    })
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                message_text = data.get("message", raw)
            except json.JSONDecodeError:
                message_text = raw
            await manager.broadcast({
                "type": "message",
                "sender": user_id,
                "message": message_text
            })
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.broadcast({
            "type": "system",
            "message": f"{user_id} ha salido del chat.",
            "sender": "system"
        })
