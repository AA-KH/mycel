"""
Developer Agent
An agent specialized in software engineering, API development, and frontend/backend tasks.
"""
import uuid
from datetime import datetime, timezone
import logging
from typing import Dict, Any, List, Optional

from agents.runtime.result import ToolRequest, ToolResult
from tools.gateway import CoreToolGateway

logger = logging.getLogger(__name__)

class DeveloperAgent:
    """
    AI Agent for the Developer team.
    Produces:
    - Code (Python, TypeScript, HTML/CSS)
    - System Designs
    - Debugging & Refactoring
    """

    def __init__(self, employee_id: str = "emp_dev_backend_001"):
        self.employee_id = employee_id
        self.session_id = str(uuid.uuid4())
        self.tool_gateway = CoreToolGateway()
        
        self.developer_skills = [
            "api_development", "backend_development", "frontend_development",
            "database_management", "software_architecture", "debugging",
            "testing", "version_control"
        ]
        
        self.developer_tools = [
            "code.generator",
            "code.executor", 
            "code.tester",
            "filesystem.read",
            "filesystem.write",
            "terminal.execute"
        ]

    async def develop_code(
        self,
        task_description: str,
        skill_type: str,
        context: str = "",
    ) -> Dict[str, Any]:
        """
        Generate software code for a given task.
        """
        logger.info(f"[DeveloperAgent] develop_code | skill={skill_type} | task={task_description[:60]}")
        request = ToolRequest(
            tool_name="code.generator",
            employee_id=self.employee_id,
            execution_id=self.session_id,
            arguments={
                "task_description": task_description,
                "skill_type": skill_type,
                "context": context,
            }
        )
        result = await self.tool_gateway.execute(request)
        if result.status == "success":
            return {
                "status": "success",
                "code": result.output.get("code", ""),
                "explanation": result.output.get("explanation", ""),
                "language": result.output.get("language", "python"),
                "skill_type": skill_type,
                "session_id": self.session_id,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        logger.error(f"[DeveloperAgent] Code generation failed: {result.error}")
        return {"status": "error", "error": result.error, "session_id": self.session_id}

    async def execute_code(
        self,
        code: str,
        test_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Safely execute generated code."""
        logger.info(f"[DeveloperAgent] execute_code")
        request = ToolRequest(
            tool_name="code.executor",
            employee_id=self.employee_id,
            execution_id=self.session_id,
            arguments={
                "code": code,
                "test_data": test_data or {}
            }
        )
        result = await self.tool_gateway.execute(request)
        if result.status == "success":
            return {
                "status": "success",
                "result": result.output.get("result", ""),
                "variables": result.output.get("variables", {}),
                "session_id": self.session_id
            }
        return {"status": "error", "error": result.error, "session_id": self.session_id}
