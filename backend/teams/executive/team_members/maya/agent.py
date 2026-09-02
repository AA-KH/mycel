import json
from core.mongodb import mongodb_connection
from teams.architecture.base import ArchitectureBaseAgent
from .prompt import SYSTEM_PROMPT
from .profile import NAME, ROLE
from .tools import get_tools

class MayaHRAgent(ArchitectureBaseAgent):
    def __init__(self, session_id: str = None):
        super().__init__(
            name=NAME,
            role=ROLE,
            system_prompt=SYSTEM_PROMPT,
            agent_tools=get_tools(),
            session_id=session_id
        )
        self.hired_team = None

    async def execute_tool(self, tool_name: str, kwargs: dict) -> str:
        if tool_name == "query_available_agents":
            return await self._query_available_agents()
        elif tool_name == "hire_team":
            return await self._hire_team(kwargs.get("hired_personnel", []), kwargs.get("reasoning", ""))
        else:
            return f"Error: Tool {tool_name} not found."

    async def _query_available_agents(self) -> str:
        try:
            db = mongodb_connection.db
            agents = await db.agents.find({}, {"_id": 0}).to_list(length=100)
            return json.dumps(agents, indent=2)
        except Exception as e:
            return f"Error fetching agents from DB: {str(e)}"

    async def _hire_team(self, hired_personnel: list, reasoning: str) -> str:
        # Save it to the instance so project.py can read it directly without regex parsing
        self.hired_team = hired_personnel
        return json.dumps({
            "status": "success",
            "hired_personnel": hired_personnel,
            "reasoning": reasoning
        })
