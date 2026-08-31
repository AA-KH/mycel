from workforce.employees.models import ToolPermission

tools = [
    "filesystem.read",
    "filesystem.write",
    "terminal.execute",
    "browser.devtools",
    "database.query",
    "git.operations"
]

permissions = {
    "filesystem.read": ToolPermission.ALLOWED,
    "filesystem.write": ToolPermission.ALLOWED,
    "terminal.execute": ToolPermission.ALLOWED,
    "browser.devtools": ToolPermission.ALLOWED,
    "database.query": ToolPermission.ALLOWED,
    "git.operations": ToolPermission.ALLOWED
}
