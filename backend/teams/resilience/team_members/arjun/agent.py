from teams.resilience.base import ResilienceBaseAgent
from teams.resilience.team_members.arjun.prompt import ARJUN_SYSTEM_PROMPT
from teams.resilience.team_members.arjun.tools import ARJUN_SPECIFIC_TOOLS, generate_recovery_plan, fetch_live_exchange_rate

class ArjunAgent(ResilienceBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Arjun",
            role="Business Continuity & Recovery Planner",
            system_prompt=ARJUN_SYSTEM_PROMPT,
            tools=ARJUN_SPECIFIC_TOOLS,
            user_id=task_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "generate_recovery_plan":
            return await generate_recovery_plan(
                arguments.get("incident_name", "Unknown Incident"),
                arguments.get("alternative_suppliers", []),
                arguments.get("freight_mode", ""),
                arguments.get("total_mitigation_cost", 0.0),
                arguments.get("financial_loss_prevented", 0.0)
            )
        elif function_name == "fetch_live_exchange_rate":
            return await fetch_live_exchange_rate(
                arguments.get("base_currency", ""),
                arguments.get("amount", 0.0),
                arguments.get("target_currency", "USD")
            )
        
        # Fallback to shared tools in ResilienceBaseAgent
        # (calculate_financial_impact, search_alternate_suppliers, estimate_emergency_freight)
        return await super().execute_tool(function_name, arguments)
