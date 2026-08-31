from workforce.employees.models import ToolPermission

tools = [
    "filesystem.read",
    "filesystem.write", 
    "terminal.execute",
    "database.query",
    "git.operations"
]

permissions = {
    "filesystem.read": ToolPermission.ALLOWED,
    "filesystem.write": ToolPermission.ALLOWED,
    "terminal.execute": ToolPermission.ALLOWED,
    "database.query": ToolPermission.ALLOWED,
    "git.operations": ToolPermission.ALLOWED
}
