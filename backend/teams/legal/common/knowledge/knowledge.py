# Individual knowledge space definitions
from .individual.indian_legal_system import indian_legal_system
from .individual.indian_statutes import indian_statutes
from .individual.indian_regulations import indian_regulations
from .individual.indian_case_law import indian_case_law
from .individual.legal_terminology import legal_terminology

# Core knowledge spaces (essential for legal team)
CORE_KNOWLEDGE = [
    indian_legal_system,
    indian_statutes,
    indian_regulations,
    indian_case_law,
    legal_terminology
]

# All legal knowledge including specialized areas
LEGAL_KNOWLEDGE = CORE_KNOWLEDGE
