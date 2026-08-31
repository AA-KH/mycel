from .base import ReasoningStrategy
from .general import GeneralReasoningStrategy
from .research import ResearchVerifyStrategy
from .coding import CodeTestStrategy
from .creative import CreativeReviewStrategy
from ..llm_adapter import LLMReasoner

VALID_STRATEGIES = {
    "general_problem_solving": GeneralReasoningStrategy,
    "research_verify": ResearchVerifyStrategy,
    "code_test": CodeTestStrategy,
    "creative_review": CreativeReviewStrategy
}

def get_strategy(strategy_name: str, llm: LLMReasoner) -> ReasoningStrategy:
    """
    Factory function to map a string name from Employee.reasoning_profile
    to the correct ReasoningStrategy implementation.
    """
    cls = VALID_STRATEGIES.get(strategy_name)
    if not cls:
        raise ValueError(f"Unknown reasoning strategy: {strategy_name}")
    return cls(llm)
