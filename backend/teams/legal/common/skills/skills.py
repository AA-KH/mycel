# Individual skill definitions
from .individual.legal_research import legal_research
from .individual.document_analysis import document_analysis
from .individual.contract_analysis import contract_analysis
from .individual.compliance_analysis import compliance_analysis
from .individual.legal_writing import legal_writing
from .individual.citation_validation import citation_validation

# Core skills (most important for legal team)
CORE_SKILLS = [
    legal_research,
    document_analysis,
    contract_analysis,
    compliance_analysis,
    legal_writing,
    citation_validation
]

# All legal skills including specialized ones
LEGAL_SKILLS = CORE_SKILLS
