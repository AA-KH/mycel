from teams.council.base import CouncilBaseAgent
from teams.council.team_members.omar.prompt import OMAR_SYSTEM_PROMPT
from teams.council.team_members.omar.tools import OMAR_SPECIFIC_TOOLS, run_regulatory_compliance_audit

class OmarAgent(CouncilBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Omar",
            role="Risk & Compliance Strategist (Council)",
            system_prompt=OMAR_SYSTEM_PROMPT,
            tools=OMAR_SPECIFIC_TOOLS,
            user_id=task_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "run_regulatory_compliance_audit":
            return await run_regulatory_compliance_audit(
                arguments.get("vendor_name", ""),
                arguments.get("country", ""),
                arguments.get("industry", ""),
                arguments.get("processes_eu_citizen_data", False),
                arguments.get("has_anti_bribery_policy", False),
                arguments.get("has_conflict_minerals_declaration", False),
                arguments.get("has_reach_rohs_certification", False),
                arguments.get("has_child_labor_audit", False)
            )
        return await super().execute_tool(function_name, arguments)
