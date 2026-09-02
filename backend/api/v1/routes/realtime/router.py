"""
Real-time WebSockets for agent status updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict
import time
from core.logger import logger
from core.mongodb import mongodb_connection
from core.auth import get_current_user

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # project_id -> list of WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        logger.info(f"New WebSocket connection established for project {project_id}")

    def disconnect(self, websocket: WebSocket, project_id: str):
        if project_id in self.active_connections and websocket in self.active_connections[project_id]:
            self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
            logger.info(f"WebSocket disconnected from project {project_id}")

    async def broadcast(self, project_id: str, message: dict):
        if project_id in self.active_connections:
            connections = self.active_connections[project_id]
            logger.debug(f"Broadcasting message to {len(connections)} clients for project {project_id}")
            for connection in list(connections):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client, removing connection: {e}")
                    self.disconnect(connection, project_id)

manager = ConnectionManager()

@router.websocket("/sessions/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await manager.connect(websocket, project_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)

@router.post("/broadcast/{project_id}")
async def broadcast_endpoint(project_id: str, message: dict):
    await manager.broadcast(project_id, message)
    return {"status": "ok"}
    
@router.get("/snapshot/{project_id}")
async def get_snapshot(project_id: str, _ = Depends(get_current_user)):
    """
    Returns the accumulated MissionState for the frontend Pixel Office.
    Reduces events from project_events into a MissionState format.
    """
    db = mongodb_connection.db
    
    # Check if project exists
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        return {"error": "Project not found"}
        
    created_at = project.get("created_at")
    if created_at:
        start_time = created_at.timestamp() * 1000
    elif hasattr(project.get("_id"), "generation_time"):
        start_time = project["_id"].generation_time.timestamp() * 1000
    else:
        start_time = time.time() * 1000
        
    events = await db.project_events.find({"project_id": project_id}).sort("at", 1).to_list(length=None)
    
    # Build MissionState
    state = {
        "clock": int(time.time() * 1000) - int(start_time),
        "logs": [],
        "hires": [],
        "agents": {},
        "complete": project.get("status") == "COMPLETED",
        "architecture_report": project.get("architecture_report") if project.get("status") == "COMPLETED" else None
    }
    
    for idx, e in enumerate(events):
        kind = e["kind"]
        data = e["data"]
        
        if kind == "log":
            state["logs"].append({
                "id": idx,
                "at": e["at"] - start_time,
                "level": data.get("level", "info"),
                "text": data.get("text", "")
            })
        elif kind == "hire":
            state["hires"].append({
                "id": idx,
                "at": e["at"] - start_time,
                "agent": data.get("agent"),
                "team": data.get("team"),
                "role": data.get("role"),
                "badge": data.get("badge", ""),
                "clearance": data.get("clearance", "GREEN"),
                "mandate": data.get("mandate", "")
            })
            state["agents"][data["agent"]] = {
                "name": data["agent"],
                "phase": "hired",
                "task": "Awaiting assignment",
                "startedAt": None,
                "finishedAt": None
            }
        elif kind == "start":
            agent = data["agent"]
            if agent not in state["agents"]:
                state["agents"][agent] = {"name": agent}
            state["agents"][agent].update({
                "phase": "working",
                "task": data.get("task", ""),
                "startedAt": e["at"] - start_time
            })
        elif kind == "finish":
            agent = data["agent"]
            if agent in state["agents"]:
                state["agents"][agent].update({
                    "phase": "done",
                    "finishedAt": e["at"] - start_time
                })
        elif kind == "complete":
            state["complete"] = True
            
    return state
