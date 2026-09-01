from teams.network.base import NetworkBaseAgent, NETWORK_TOOLS, MATH_REASONING_INSTRUCTIONS
from teams.network.team_members.aanya.prompt import AANYA_SYSTEM_PROMPT
from teams.network.team_members.aanya.tools import AANYA_SPECIFIC_TOOLS, calculate_center_of_gravity, estimate_facility_cost

class AanyaAgent(NetworkBaseAgent):
    def __init__(self, task_id: str = "default", session_id: str = None):
        system_prompt = f"{AANYA_SYSTEM_PROMPT}\n\n{MATH_REASONING_INSTRUCTIONS}"
        
        # Combine base network tools with Aanya's specific tools
        combined_tools = NETWORK_TOOLS + AANYA_SPECIFIC_TOOLS
        
        super().__init__(
            name="Aanya",
            role="Network Architect",
            system_prompt=system_prompt,
            user_id=task_id,
            tools=combined_tools,
            session_id=session_id
        )
        
    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        # Override to handle Aanya's specific tools first
        if function_name == "calculate_center_of_gravity":
            return await calculate_center_of_gravity(
                arguments.get("cities", []),
                arguments.get("weights", [])
            )
        elif function_name == "estimate_facility_cost":
            return await estimate_facility_cost(
                arguments.get("region", ""),
                arguments.get("size_sqm", 0.0),
                arguments.get("facility_type", "")
            )
        elif function_name == "calculate_driving_route":
            # Note: need to import calculate_driving_route above
            from teams.network.team_members.aanya.tools import calculate_driving_route
            return await calculate_driving_route(
                arguments.get("city1", ""),
                arguments.get("city2", "")
            )
        elif function_name == "get_regional_economic_data":
            # Note: need to import get_regional_economic_data above
            from teams.network.team_members.aanya.tools import get_regional_economic_data
            return await get_regional_economic_data(
                arguments.get("country_code", "")
            )
        
        # Fallback to base network tools (like calculate_distance)
        return await super().execute_tool(function_name, arguments)
