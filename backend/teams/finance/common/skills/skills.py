# Individual skill definitions
from .individual.accounting import accounting
from .individual.financial_modeling import financial_modeling
from .individual.budgeting import budgeting
from .individual.data_analysis import data_analysis
from .individual.reconciliation import reconciliation
from .individual.financial_reporting import financial_reporting
from .individual.forecasting import forecasting
from .individual.risk_assessment import risk_assessment
from .individual.compliance import compliance
from .individual.cost_analysis import cost_analysis

# Core skills (most important for finance team)
CORE_SKILLS = [
    accounting,
    financial_modeling,
    budgeting,
    data_analysis,
    reconciliation,
    financial_reporting,
    forecasting
]

# All finance skills including specialized ones
FINANCE_SKILLS = CORE_SKILLS + [
    risk_assessment,
    compliance,
    cost_analysis
]
