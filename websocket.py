from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException
from typing import Dict, Set, List
import json
import logging
from app.features.user.repositories.user_repository import UserRepository

router = APIRouter()
logger = logging.getLogger(__name__)


def get_user_or_none(user_id: int):
    """Buscar usuario en BD por ID"""
    try:
        repo = UserRepository()
        return repo.get_user_by_id(user_id)
    except Exception:
        return None


class StreamManager:
    def __init__(self):
        # streamer_id -> {"streamer": User, "viewers": Set[WebSocket]}
        self.active_streams: Dict[int, dict] = {}
        # user_id -> WebSocket (para streamers)
        self.streamer_connections: Dict[int, WebSocket] = {}
        # seguimiento de quiénes siguen a quiénes
        self.followers: Dict[int, Set[int]] = {}  # streamer_id -> {follower_ids}

    def add_follower(self, follower_id: int, streamer_id: int):
        """Agregar seguidor a streamer"""
        if streamer_id not in self.followers:
            self.followers[streamer_id] = set()
        self.followers[streamer_id].add(follower_id)

    def is_follower(self, follower_id: int, streamer_id: int) -> bool:
        """Verificar si un usuario sigue a un streamer"""
        return streamer_id in self.followers and follower_id in self.followers[streamer_id]

    async def start_stream(self, streamer_id: int, websocket: WebSocket, username: str):
        """Iniciar stream de un streamer"""
        await websocket.accept()
        self.streamer_connections[streamer_id] = websocket
        self.active_streams[streamer_id] = {
            "username": username,
            "viewers": set()
        }
        logger.info(f"Streamer {username} (ID: {streamer_id}) inició stream")

    async def join_stream(self, viewer_id: int, streamer_id: int, websocket: WebSocket) -> bool:
        """Que un viewer se una a un stream"""
        if streamer_id not in self.active_streams:
            return False  # Stream no existe

        await websocket.accept()
        self.active_streams[streamer_id]["viewers"].add(websocket)
        logger.info(f"Viewer {viewer_id} se unió al stream de {streamer_id}")
        return True

    async def broadcast_to_stream(self, streamer_id: int, message: dict, exclude_ws: WebSocket = None):
        """Enviar mensaje a TODOS en el stream (streamer + viewers)"""
        if streamer_id not in self.active_streams:
            return

        # Enviar al streamer
        streamer_ws = self.streamer_connections.get(streamer_id)
        if streamer_ws and streamer_ws != exclude_ws:
            try:
                await streamer_ws.send_json(message)
            except Exception:
                pass

        # Enviar a todos los viewers
        disconnected = []
        for viewer_ws in self.active_streams[streamer_id]["viewers"]:
            if viewer_ws == exclude_ws:
                continue
            try:
                await viewer_ws.send_json(message)
            except Exception:
                disconnected.append(viewer_ws)

        for ws in disconnected:
            self.active_streams[streamer_id]["viewers"].discard(ws)

    def disconnect_streamer(self, streamer_id: int):
        """Desconectar streamer y cerrar su stream"""
        if streamer_id in self.streamer_connections:
            del self.streamer_connections[streamer_id]
        if streamer_id in self.active_streams:
            del self.active_streams[streamer_id]
        logger.info(f"Streamer {streamer_id} desconectado")

    def disconnect_viewer(self, streamer_id: int, websocket: WebSocket):
        """Remover viewer del stream"""
        if streamer_id in self.active_streams:
            self.active_streams[streamer_id]["viewers"].discard(websocket)

    def get_active_streams(self) -> List[dict]:
        """Obtener lista de streams activos"""
        return [
            {
                "streamer_id": sid,
                "username": info["username"],
                "viewers_count": len(info["viewers"])
            }
            for sid, info in self.active_streams.items()
        ]


manager = StreamManager()


@router.websocket("/ws/stream/{streamer_id}")
async def stream_endpoint(websocket: WebSocket, streamer_id: int):
    """
    SOLO PARA STREAMERS: Endpoint para iniciar/mantener un stream
    """
    # Verificar que el usuario existe y es streamer
    user = get_user_or_none(streamer_id)
    if not user:
        await websocket.close(code=4004, reason="Usuario no encontrado")
        return
    if user.rol != 'streamer':
        await websocket.close(code=4003, reason="Solo los streamers pueden iniciar un stream")
        return

    await manager.start_stream(streamer_id, websocket, username=user.username)

    # Notificar a todos que el stream inició
    await manager.broadcast_to_stream(streamer_id, {
        "type": "system",
        "message": f"{user.username} ha iniciado el stream."
    })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                message = {"content": data}

            # Enviar mensaje a todos los viewers
            await manager.broadcast_to_stream(streamer_id, {
                "type": "stream_message",
                "sender": user.username,
                "message": message
            })

    except WebSocketDisconnect:
        # Notificar que el stream terminó
        await manager.broadcast_to_stream(streamer_id, {
            "type": "system",
            "message": f"{user.username} ha terminado el stream."
        })
        manager.disconnect_streamer(streamer_id)
        logger.info(f"Streamer {user.username} desconectado")


@router.websocket("/ws/watch/{streamer_id}/{viewer_id}")
async def watch_stream_endpoint(websocket: WebSocket, streamer_id: int, viewer_id: int):
    """
    PARA FOLLOWERS: Conectarse a un stream de un streamer
    """
    # Verificar que el viewer existe
    viewer = get_user_or_none(viewer_id)
    if not viewer:
        await websocket.close(code=4004, reason="Usuario no encontrado")
        return

    # Verificar que el streamer existe
    streamer = get_user_or_none(streamer_id)
    if not streamer:
        await websocket.close(code=4004, reason="Streamer no encontrado")
        return

    # Verificar si el stream está activo
    if streamer_id not in manager.active_streams:
        await websocket.close(code=4001, reason="Stream no disponible")
        return

    # Conectarse al stream
    success = await manager.join_stream(viewer_id, streamer_id, websocket)
    if not success:
        await websocket.close(code=4001, reason="No se pudo unir al stream")
        return

    # Notificar que el viewer se unió
    await manager.broadcast_to_stream(streamer_id, {
        "type": "system",
        "message": f"{viewer.username} se ha unido al chat."
    })

    try:
        while True:
            # El viewer envía mensajes de chat
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                message = {"content": data}

            # Reenviar mensaje a TODOS (streamer + viewers)
            await manager.broadcast_to_stream(streamer_id, {
                "type": "chat_message",
                "sender": viewer.username,
                "message": message
            })

    except WebSocketDisconnect:
        manager.disconnect_viewer(streamer_id, websocket)
        await manager.broadcast_to_stream(streamer_id, {
            "type": "system",
            "message": f"{viewer.username} ha salido del chat."
        })
        logger.info(f"Viewer {viewer.username} salió del stream")



