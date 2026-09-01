from teams.council.base import CouncilBaseAgent
from teams.council.team_members.sofia.prompt import SOFIA_SYSTEM_PROMPT
from teams.council.team_members.sofia.tools import SOFIA_SPECIFIC_TOOLS, draft_council_resolution

class SofiaAgent(CouncilBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Sofia",
            role="Council Chair",
            system_prompt=SOFIA_SYSTEM_PROMPT,
            tools=SOFIA_SPECIFIC_TOOLS,
            user_id=task_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "draft_council_resolution":
            return await draft_council_resolution(
                arguments.get("subject", ""),
                arguments.get("council_decision", "DEFERRED"),
                arguments.get("rationale", ""),
                arguments.get("member_votes", {}),
                arguments.get("conditions", []),
                arguments.get("review_days", 90)
            )
        return await super().execute_tool(function_name, arguments)
