from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json
from core.mongodb import mongodb_connection
from api.v1.routes.realtime import manager
from core.logger import logger

class RuntimeEventPublisher:
    """
    Handles persisting agent executions and publishing real-time events.
    """
    
    @staticmethod
    async def publish_state_change(
        execution_id: str,
        task_id: str,
        employee_id: str,
        company_id: str,
        new_state: str,
        summary: str,
        user_id: Optional[str] = None
    ):
        now = datetime.now(timezone.utc)
        db = mongodb_connection.db
        
        # 1. Update Execution Persistence Collection (agent_executions)
        execution_data = {
            "execution_id": execution_id,
            "task_id": task_id,
            "employee_id": employee_id,
            "company_id": company_id,
            "status": new_state.lower(),
            "last_updated_at": now
        }
        
        if new_state == "CREATED":
            execution_data["created_at"] = now
            
        try:
            # We assume agent_executions collection exists or will be created dynamically
            await db.agent_executions.update_one(
                {"execution_id": execution_id},
                {"$set": execution_data},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Failed to persist execution {execution_id}: {e}")
            
        # 2. Update Legacy / Realtime Collection (agent_sessions / WebSockets)
        # To maintain compatibility with existing Pixel Office frontend
        session_data = {
            "api_key_id": "internal_groq_agent",
            "user_id": user_id or "system",
            "session_id": execution_id,
            "role": "employee", # Generic employee role
            "employee_id": employee_id,
            "status": "working" if new_state not in ["COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"] else new_state.lower(),
            "summary": summary[:160],
            "link": None,
            "workspace": "Agent Runtime",
            "last_heartbeat_at": now
        }
        
        try:
            await db.agent_sessions.update_one(
                {"session_id": execution_id},
                {"$set": session_data},
                upsert=True
            )
            
            ws_data = session_data.copy()
            ws_data["last_heartbeat_at"] = ws_data["last_heartbeat_at"].isoformat()
            ws_data["event"] = f"agent.execution.{new_state.lower()}"
            await manager.broadcast(task_id, ws_data)
        except Exception as e:
            logger.error(f"Failed to report realtime status: {e}")
            
    @staticmethod
    async def publish_completion(
        execution_id: str,
        result: Any
    ):
        db = mongodb_connection.db
        now = datetime.now(timezone.utc)
        try:
            # Result is ExecutionResult object, dump it to dict
            result_dict = result.model_dump()
            await db.agent_executions.update_one(
                {"execution_id": execution_id},
                {
                    "$set": {
                        "status": result.status,
                        "completed_at": now,
                        "metrics": result.metrics,
                        "error_code": result.error,
                        "verification_status": result.verification.status
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to save completion execution {execution_id}: {e}")
