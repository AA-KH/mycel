import uuid
from datetime import datetime, timezone
import logging

from core.mongodb import mongodb_connection
from api.v1.routes.realtime import manager
from core.config import settings
from core.groq_engine import groq_engine

logger = logging.getLogger(__name__)

class BaseAgent:
    """
    DEPRECATED: Base Agent
    Provides the foundational logic for legacy agents.
    Slated for complete removal once the new AgentRuntime fully subsumes all execution lifecycles.
    """
    def __init__(self, name: str, role: str, system_prompt: str, user_id: str = "system"):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id

    async def report_status(self, state: str, summary: str, event_type: str = "status_update", break_activity: str | None = None):
        """Report status directly to the MongoDB and WebSockets (Virtual Office UI)"""
        now = datetime.now(timezone.utc)
        db = mongodb_connection.db

        session_data = {
            "api_key_id": "internal_groq_agent",
            "user_id": self.user_id,
            "session_id": self.session_id,
            "role": self.role,
            "status": state,
            "summary": summary, # Send FULL logs without truncation for frontend transparency
            "link": None,
            "workspace": "Groq Engine",
            "last_heartbeat_at": now,
            "break_activity": break_activity,
            "team": getattr(self, 'team', None),
            "employee_name": getattr(self, 'employee_name', self.name),
        }

        try:
            await db.agent_sessions.update_one(
                {"session_id": self.session_id},
                {"$set": session_data},
                upsert=True
            )
            
            ws_data = session_data.copy()
            ws_data["last_heartbeat_at"] = ws_data["last_heartbeat_at"].isoformat()
            ws_data["event"] = event_type
            import httpx
            try:
                async with httpx.AsyncClient() as client:
                    await client.post("http://127.0.0.1:8000/api/v1/broadcast", json=ws_data)
            except Exception as e:
                logger.error(f"Failed to broadcast status: {e}")
        except Exception as e:
            logger.error(f"Failed to report status: {e}")

    async def run_task(self, task_description: str, model: str = "qwen/qwen3.8-27b"):
        """Execute a task using the Groq LLM with failover engine"""

        await self.report_status("working", f"Thinking about: {task_description[:50]}...")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task_description}
        ]

        try:
            response = await groq_engine.chat_completion(
                model=model,
                messages=messages,
                temperature=0.7
            )
            raw_result = response.choices[0].message.content or ""
            import re
            result = re.sub(r'<think>.*?</think>', '', raw_result, flags=re.DOTALL).strip()
            await self.report_status("complete", "Task finished successfully.")
            return result
        except Exception as e:
            await self.report_status("failure", f"Task failed: {str(e)[:50]}")
            raise e
