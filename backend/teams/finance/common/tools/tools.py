# Individual tool definitions
from .individual.spreadsheet_processing import spreadsheet_processing
from .individual.financial_calculator import financial_calculator
from .individual.data_analysis_tools import data_analysis_tools
from .individual.document_generation import document_generation
from .individual.database_query import database_query
from .individual.reporting_tools import reporting_tools

# Core tools (essential for finance team)
CORE_TOOLS = [
    spreadsheet_processing,
    financial_calculator,
    data_analysis_tools,
    document_generation,
    reporting_tools
]

# All finance tools including specialized ones
FINANCE_TOOLS = CORE_TOOLS + [
    database_query
]
