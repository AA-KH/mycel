from teams.council.base import CouncilBaseAgent
from teams.council.team_members.helena.prompt import HELENA_SYSTEM_PROMPT
from teams.council.team_members.helena.tools import HELENA_SPECIFIC_TOOLS, benchmark_supplier_cost

class HelenaAgent(CouncilBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Helena",
            role="Cost Strategist (Council)",
            system_prompt=HELENA_SYSTEM_PROMPT,
            tools=HELENA_SPECIFIC_TOOLS,
            user_id=task_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "benchmark_supplier_cost":
            return await benchmark_supplier_cost(
                arguments.get("supplier_name", ""),
                arguments.get("product_category", ""),
                arguments.get("quoted_price_per_unit", 0.0),
                arguments.get("volume_units_per_year", 0.0)
            )
        return await super().execute_tool(function_name, arguments)
