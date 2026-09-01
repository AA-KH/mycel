from teams.network.base import NetworkBaseAgent, NETWORK_TOOLS, MATH_REASONING_INSTRUCTIONS
from teams.network.team_members.tara.prompt import TARA_SYSTEM_PROMPT

class TaraAgent(NetworkBaseAgent):
    def __init__(self, task_id: str = "default"):
        system_prompt = f"{TARA_SYSTEM_PROMPT}\n\n{MATH_REASONING_INSTRUCTIONS}"
        super().__init__(
            name="Tara",
            role="Operations Scheduler",
            system_prompt=system_prompt,
            user_id=task_id,
            tools=NETWORK_TOOLS
        )
