# Individual reasoning strategy definitions
from .individual.engineering_reasoning import engineering_reasoning
from .individual.code_test import code_test
from .individual.security_first import security_first
from .individual.design_implement_review import design_implement_review
from .individual.plan_validate_execute import plan_validate_execute

# Core reasoning strategies (essential for developer team)
CORE_REASONING = [
    engineering_reasoning,
    code_test
]

# All engineering reasoning strategies including specialized approaches
ENGINEERING_REASONING = CORE_REASONING + [
    security_first,
    design_implement_review,
    plan_validate_execute
]
