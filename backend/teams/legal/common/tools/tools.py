# Individual tool definitions
from .individual.legal_document_parser import legal_document_parser
from .individual.rag_retrieval import rag_retrieval
from .individual.document_search import document_search
from .individual.citation_tools import citation_tools
from .individual.document_generation import document_generation

# Core tools (essential for legal team)
CORE_TOOLS = [
    legal_document_parser,
    rag_retrieval,
    document_search,
    citation_tools,
    document_generation
]

# All legal tools including specialized ones
LEGAL_TOOLS = CORE_TOOLS
