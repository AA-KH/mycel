from teams.architecture.base import ArchitectureBaseAgent
from .profile import NAME, ROLE
from .prompt import SYSTEM_PROMPT
from .tools import get_tools

class PriyaAgent(ArchitectureBaseAgent):
    def __init__(self):
        super().__init__(
            name=NAME,
            role=ROLE,
            system_prompt=SYSTEM_PROMPT,
            agent_tools=get_tools()
        )
