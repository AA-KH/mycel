# Individual reasoning strategy definitions
from .individual.financial_validation import financial_validation
from .individual.financial_analysis_reasoning import financial_analysis_reasoning
from .individual.budget_optimization import budget_optimization

# Core reasoning strategies (essential for finance team)
CORE_REASONING = [
    financial_validation,
    financial_analysis_reasoning
]

# All finance reasoning strategies including specialized approaches
FINANCE_REASONING = CORE_REASONING + [
    budget_optimization
]
