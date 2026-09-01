from teams.network.base import NetworkBaseAgent, NETWORK_TOOLS, MATH_REASONING_INSTRUCTIONS
from teams.network.team_members.tara.prompt import TARA_SYSTEM_PROMPT
from teams.network.team_members.tara.tools import TARA_SPECIFIC_TOOLS, calculate_storage_utilization, schedule_dock_appointments, calculate_throughput_bottleneck

class TaraAgent(NetworkBaseAgent):
    def __init__(self, task_id: str = "default"):
        system_prompt = f"{TARA_SYSTEM_PROMPT}\n\n{MATH_REASONING_INSTRUCTIONS}"
        
        # Combine base network tools with Tara's specific tools
        combined_tools = NETWORK_TOOLS + TARA_SPECIFIC_TOOLS
        
        super().__init__(
            name="Tara",
            role="Operations Scheduler",
            system_prompt=system_prompt,
            user_id=task_id,
            tools=combined_tools
        )
        
    async def execute_tool(self, function_name: str, arguments: dict) -> str:
        # Override to handle Tara's specific tools first
        if function_name == "calculate_storage_utilization":
            return await calculate_storage_utilization(
                arguments.get("total_pallet_positions", 0),
                arguments.get("current_inventory_pallets", 0),
                arguments.get("incoming_pallets", 0)
            )
        elif function_name == "schedule_dock_appointments":
            return await schedule_dock_appointments(
                arguments.get("inbound_trucks", 0),
                arguments.get("dock_doors", 0),
                arguments.get("unload_time_hours", 0.0),
                arguments.get("working_hours", 0.0)
            )
        elif function_name == "calculate_throughput_bottleneck":
            return await calculate_throughput_bottleneck(
                arguments.get("inbound_rate", 0.0),
                arguments.get("putaway_rate", 0.0),
                arguments.get("picking_rate", 0.0),
                arguments.get("outbound_rate", 0.0)
            )
        
        # Fallback to base network tools
        return await super().execute_tool(function_name, arguments)
