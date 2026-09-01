from teams.resilience.base import ResilienceBaseAgent
from teams.resilience.team_members.vikram.prompt import VIKRAM_SYSTEM_PROMPT
from teams.resilience.team_members.vikram.tools import VIKRAM_SPECIFIC_TOOLS, plan_emergency_rerouting, evaluate_backup_capacity

class VikramAgent(ResilienceBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Vikram",
            role="Business Continuity Planner",
            system_prompt=VIKRAM_SYSTEM_PROMPT,
            user_id=task_id,
            tools=VIKRAM_SPECIFIC_TOOLS
        )
        
    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        if function_name == "plan_emergency_rerouting":
            return await plan_emergency_rerouting(
                arguments.get("origin", ""),
                arguments.get("destination", ""),
                arguments.get("blocked_node", "")
            )
        elif function_name == "evaluate_backup_capacity":
            return await evaluate_backup_capacity(
                arguments.get("supplier_name", ""),
                arguments.get("required_units", 0)
            )
        
        # Fallback to shared resilience tools
        return await super().execute_tool(function_name, arguments)
