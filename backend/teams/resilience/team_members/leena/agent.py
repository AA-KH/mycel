from teams.resilience.base import ResilienceBaseAgent
from teams.resilience.team_members.leena.prompt import LEENA_SYSTEM_PROMPT
from teams.resilience.team_members.leena.tools import LEENA_SPECIFIC_TOOLS, run_capacity_stress_test, simulate_lead_time_shock, generate_breaking_point_report

class LeenaAgent(ResilienceBaseAgent):
    def __init__(self, task_id: str = "default", session_id: str = None):
        super().__init__(
            name="Leena",
            role="Supply Chain Stress Tester",
            system_prompt=LEENA_SYSTEM_PROMPT,
            tools=LEENA_SPECIFIC_TOOLS,
            user_id=task_id,
            session_id=session_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "run_capacity_stress_test":
            return await run_capacity_stress_test(
                arguments.get("network_capacity", []),
                arguments.get("surge_multiplier", 1.0)
            )
        elif function_name == "simulate_lead_time_shock":
            return await simulate_lead_time_shock(
                arguments.get("daily_consumption_rate", 0.0),
                arguments.get("current_inventory", 0.0),
                arguments.get("expected_delay_days", 0.0)
            )
        elif function_name == "generate_breaking_point_report":
            return await generate_breaking_point_report(
                arguments.get("failed_nodes", []),
                arguments.get("days_to_stockout", 0.0),
                arguments.get("system_status", "")
            )
        
        return await super().execute_tool(function_name, arguments)
