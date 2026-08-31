from workforce.employees.models import ToolPermission

tools = [
    "finance.analyst",
    "finance.reporter",
    "spreadsheet.processing",
    "financial.calculator",
    "data.analysis",
    "reporting.tools",
]

permissions = {t: ToolPermission.ALLOWED for t in tools}
