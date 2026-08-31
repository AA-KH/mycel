from workforce.employees.models import ToolPermission

tools = [
    "finance.analyst",
    "spreadsheet.processing",
    "financial.calculator",
    "reporting.tools",
    "document.generation",
]

permissions = {t: ToolPermission.ALLOWED for t in tools}
