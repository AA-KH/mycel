from teams.network.base import NetworkBaseAgent, NETWORK_TOOLS, MATH_REASONING_INSTRUCTIONS
from teams.network.team_members.kabir.prompt import KABIR_SYSTEM_PROMPT
from teams.network.team_members.kabir.tools import KABIR_SPECIFIC_TOOLS, calculate_eoq, calculate_safety_stock, estimate_fulfillment_capacity

class KabirAgent(NetworkBaseAgent):
    def __init__(self, task_id: str = "default"):
        system_prompt = f"{KABIR_SYSTEM_PROMPT}\n\n{MATH_REASONING_INSTRUCTIONS}"
        
        # Combine base network tools with Kabir's specific tools
        combined_tools = NETWORK_TOOLS + KABIR_SPECIFIC_TOOLS
        
        super().__init__(
            name="Kabir",
            role="Inventory Optimizer",
            system_prompt=system_prompt,
            user_id=task_id,
            tools=combined_tools
        )
        
    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        # Override to handle Kabir's specific tools first
        if function_name == "calculate_eoq":
            return await calculate_eoq(
                arguments.get("annual_demand", 0),
                arguments.get("order_cost", 0.0),
                arguments.get("holding_cost_per_unit", 0.0)
            )
        elif function_name == "calculate_safety_stock":
            return await calculate_safety_stock(
                arguments.get("service_level_percent", 95.0),
                arguments.get("std_dev_demand", 0.0),
                arguments.get("lead_time_days", 0.0)
            )
        elif function_name == "estimate_fulfillment_capacity":
            return await estimate_fulfillment_capacity(
                arguments.get("pickers_count", 0),
                arguments.get("items_per_picker_per_hour", 0.0),
                arguments.get("shift_hours", 0.0),
                arguments.get("number_of_shifts", 1)
            )
        
        # Fallback to base network tools (like calculate_distance)
        return await super().execute_tool(function_name, arguments)
