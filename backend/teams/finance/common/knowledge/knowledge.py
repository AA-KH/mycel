# Individual knowledge space definitions
from .individual.accounting_fundamentals import accounting_fundamentals
from .individual.financial_analysis import financial_analysis
from .individual.budgeting_principles import budgeting_principles
from .individual.financial_reporting_standards import financial_reporting_standards
from .individual.regulatory_compliance import regulatory_compliance
from .individual.financial_markets import financial_markets
from .individual.cost_management import cost_management
from .individual.audit_procedures import audit_procedures

# Core knowledge spaces (essential for finance team)
CORE_KNOWLEDGE = [
    accounting_fundamentals,
    financial_analysis,
    budgeting_principles,
    financial_reporting_standards
]

# All finance knowledge including specialized areas
FINANCE_KNOWLEDGE = CORE_KNOWLEDGE + [
    regulatory_compliance,
    financial_markets,
    cost_management,
    audit_procedures
]
