from teams.council.base import CouncilBaseAgent
from teams.council.team_members.vikram.prompt import VIKRAM_SYSTEM_PROMPT
from teams.council.team_members.vikram.tools import VIKRAM_SPECIFIC_TOOLS, score_supply_chain_resilience

class VikramAgent(CouncilBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Vikram",
            role="Resilience Strategist (Council)",
            system_prompt=VIKRAM_SYSTEM_PROMPT,
            tools=VIKRAM_SPECIFIC_TOOLS,
            user_id=task_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "score_supply_chain_resilience":
            return await score_supply_chain_resilience(
                arguments.get("product_category", ""),
                arguments.get("num_active_suppliers", 1),
                arguments.get("num_countries_sourced_from", 1),
                arguments.get("avg_lead_time_days", 30.0),
                arguments.get("safety_stock_days", 0.0),
                arguments.get("single_source_pct", 100.0)
            )
        return await super().execute_tool(function_name, arguments)
