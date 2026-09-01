from teams.network.base import NetworkBaseAgent, NETWORK_TOOLS, MATH_REASONING_INSTRUCTIONS
from teams.network.team_members.dev.prompt import DEV_SYSTEM_PROMPT
from teams.network.team_members.dev.tools import DEV_SPECIFIC_TOOLS, calculate_total_landed_cost, get_live_currency_exchange

class DevAgent(NetworkBaseAgent):
    def __init__(self, task_id: str = "default", session_id: str = None):
        system_prompt = f"{DEV_SYSTEM_PROMPT}\n\n{MATH_REASONING_INSTRUCTIONS}"
        
        # Combine base network tools with Dev's specific tools
        combined_tools = NETWORK_TOOLS + DEV_SPECIFIC_TOOLS
        
        super().__init__(
            name="Dev",
            role="Transport Planner",
            system_prompt=system_prompt,
            user_id=task_id,
            tools=combined_tools,
            session_id=session_id
        )
        
    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        # Override to handle Dev's specific tools first
        if function_name == "calculate_total_landed_cost":
            return await calculate_total_landed_cost(
                arguments.get("unit_cost", 0.0),
                arguments.get("quantity", 0),
                arguments.get("freight_cost", 0.0),
                arguments.get("customs_percent", 0.0),
                arguments.get("insurance_percent", 0.0),
                arguments.get("overhead_cost", 0.0)
            )
        elif function_name == "get_live_currency_exchange":
            return await get_live_currency_exchange(
                arguments.get("base_currency", ""),
                arguments.get("target_currency", ""),
                arguments.get("amount", 0.0)
            )
        
        # Fallback to base network tools (like calculate_distance)
        return await super().execute_tool(function_name, arguments)
