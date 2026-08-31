# Individual reasoning strategy definitions
from .individual.legal_authority_verification import legal_authority_verification
from .individual.compliance_risk_assessment import compliance_risk_assessment

# Core reasoning strategies (essential for legal team)
CORE_REASONING = [
    legal_authority_verification,
    compliance_risk_assessment
]

# All legal reasoning strategies including specialized approaches
LEGAL_REASONING = CORE_REASONING
