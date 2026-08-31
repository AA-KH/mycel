from workforce.employees.models import ToolPermission

tools = [
    "finance.analyst",
    "finance.reporter",
    "spreadsheet.processing",
    "document.generation",
    "database.query",
]

permissions = {t: ToolPermission.ALLOWED for t in tools}
