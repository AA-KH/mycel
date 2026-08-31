from .skills.skills import CORE_SKILLS
from .tools.tools import CORE_TOOLS
from .knowledge.knowledge import CORE_KNOWLEDGE
from .reasoning.reasoning import financial_validation

COMMON_SKILLS = [skill["skill_id"] for skill in CORE_SKILLS]
COMMON_TOOLS = [tool["tool_id"] if isinstance(tool, dict) else tool.definition.id for tool in CORE_TOOLS]
COMMON_KNOWLEDGE = [knowledge["knowledge_space_id"] for knowledge in CORE_KNOWLEDGE]
COMMON_REASONING = financial_validation["strategy_id"]
