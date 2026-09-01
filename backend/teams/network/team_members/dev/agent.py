from teams.network.base import NetworkBaseAgent, NETWORK_TOOLS, MATH_REASONING_INSTRUCTIONS
from teams.network.team_members.dev.prompt import DEV_SYSTEM_PROMPT

class DevAgent(NetworkBaseAgent):
    def __init__(self, task_id: str = "default"):
        system_prompt = f"{DEV_SYSTEM_PROMPT}\n\n{MATH_REASONING_INSTRUCTIONS}"
        super().__init__(
            name="Dev",
            role="Transport Planner",
            system_prompt=system_prompt,
            user_id=task_id,
            tools=NETWORK_TOOLS
        )
