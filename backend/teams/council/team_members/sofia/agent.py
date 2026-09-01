from teams.council.base import CouncilBaseAgent
from teams.council.team_members.sofia.prompt import SOFIA_SYSTEM_PROMPT
from teams.council.team_members.sofia.tools import (
    SOFIA_SPECIFIC_TOOLS,
    synthesize_council_reports,
    resolve_strategic_conflict,
    calculate_risk_adjusted_roi,
    draft_council_resolution
)

class SofiaAgent(CouncilBaseAgent):
    def __init__(self, task_id: str = "default", session_id: str = None):
        super().__init__(
            name="Sofia",
            role="Council Chair",
            system_prompt=SOFIA_SYSTEM_PROMPT,
            tools=SOFIA_SPECIFIC_TOOLS,
            user_id=task_id,
            session_id=session_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "synthesize_council_reports":
            return await synthesize_council_reports(
                arguments.get("subject", ""),
                arguments.get("helena_verdict", ""),
                arguments.get("vikram_verdict", ""),
                arguments.get("nisha_verdict", ""),
                arguments.get("omar_verdict", "")
            )
        elif function_name == "resolve_strategic_conflict":
            return await resolve_strategic_conflict(
                arguments.get("conflict_description", ""),
                arguments.get("member_1", ""),
                arguments.get("member_2", ""),
                arguments.get("company_strategic_priority", "")
            )
        elif function_name == "calculate_risk_adjusted_roi":
            return await calculate_risk_adjusted_roi(
                arguments.get("base_projected_roi_usd", 0.0),
                arguments.get("vikram_resilience_score", 0.0),
                arguments.get("nisha_feasibility_score", 0.0),
                arguments.get("omar_fine_exposure_usd", 0.0)
            )
        elif function_name == "draft_council_resolution":
            return await draft_council_resolution(
                arguments.get("subject", ""),
                arguments.get("council_decision", ""),
                arguments.get("rationale", ""),
                arguments.get("conditions", []),
                arguments.get("review_days", 90)
            )

        # Fall through to shared Council tools
        return await super().execute_tool(function_name, arguments)
