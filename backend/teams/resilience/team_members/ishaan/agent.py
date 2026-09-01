from teams.resilience.base import ResilienceBaseAgent
from teams.resilience.team_members.ishaan.prompt import ISHAAN_SYSTEM_PROMPT
from teams.resilience.team_members.ishaan.tools import ISHAAN_SPECIFIC_TOOLS, simulate_cascading_failure, run_monte_carlo_simulation, generate_black_swan_scenario, fetch_nasa_eonet_anomalies, fetch_world_bank_economic_data

class IshaanAgent(ResilienceBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Ishaan",
            role="Disruption Scenario Generator (Chaos Engineer)",
            system_prompt=ISHAAN_SYSTEM_PROMPT,
            tools=ISHAAN_SPECIFIC_TOOLS,
            user_id=task_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "simulate_cascading_failure":
            return await simulate_cascading_failure(
                arguments.get("nodes", []),
                arguments.get("edges", []),
                arguments.get("initial_failed_node", "")
            )
        elif function_name == "run_monte_carlo_simulation":
            return await run_monte_carlo_simulation(
                arguments.get("risk_events", []),
                arguments.get("iterations", 1000)
            )
        elif function_name == "generate_black_swan_scenario":
            return await generate_black_swan_scenario(
                arguments.get("industry", ""),
                arguments.get("region", "")
            )
        elif function_name == "fetch_nasa_eonet_anomalies":
            return await fetch_nasa_eonet_anomalies(
                arguments.get("limit", 5)
            )
        elif function_name == "fetch_world_bank_economic_data":
            return await fetch_world_bank_economic_data(
                arguments.get("country_code", ""),
                arguments.get("indicator", "")
            )
        
        return await super().execute_tool(function_name, arguments)
