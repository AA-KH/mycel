"""
Real-time WebSockets for agent status updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from core.logger import logger

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("New WebSocket connection established")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket disconnected")

    async def broadcast(self, message: dict):
        logger.debug(f"Broadcasting message to {len(self.active_connections)} clients")
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client, removing connection: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

@router.websocket("/sessions")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/broadcast")
async def broadcast_endpoint(message: dict):
    await manager.broadcast(message)
    return {"status": "ok"}
