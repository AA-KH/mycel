from teams.network.base import NetworkBaseAgent, NETWORK_TOOLS, MATH_REASONING_INSTRUCTIONS
from teams.network.team_members.kabir.prompt import KABIR_SYSTEM_PROMPT

class KabirAgent(NetworkBaseAgent):
    def __init__(self, task_id: str = "default"):
        system_prompt = f"{KABIR_SYSTEM_PROMPT}\n\n{MATH_REASONING_INSTRUCTIONS}"
        super().__init__(
            name="Kabir",
            role="Inventory Optimizer",
            system_prompt=system_prompt,
            user_id=task_id,
            tools=NETWORK_TOOLS
        )
