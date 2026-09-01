from teams.council.base import CouncilBaseAgent
from teams.council.team_members.nisha.prompt import NISHA_SYSTEM_PROMPT
from teams.council.team_members.nisha.tools import NISHA_SPECIFIC_TOOLS, audit_operational_efficiency

class NishaAgent(CouncilBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Nisha",
            role="Operations Strategist (Council)",
            system_prompt=NISHA_SYSTEM_PROMPT,
            tools=NISHA_SPECIFIC_TOOLS,
            user_id=task_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "audit_operational_efficiency":
            return await audit_operational_efficiency(
                arguments.get("process_name", ""),
                arguments.get("theoretical_capacity_units_per_day", 100.0),
                arguments.get("actual_output_units_per_day", 0.0),
                arguments.get("avg_cycle_time_minutes", 0.0),
                arguments.get("target_cycle_time_minutes", 0.0),
                arguments.get("defect_rate_pct", 0.0),
                arguments.get("downtime_hours_per_week", 0.0)
            )
        return await super().execute_tool(function_name, arguments)
