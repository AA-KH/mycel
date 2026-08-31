from workforce.employees.models import ToolPermission

tools = [
    "filesystem.read",
    "filesystem.write",
    "terminal.execute",
    "git.operations",
    "project_management"
]

permissions = {
    "filesystem.read": ToolPermission.ALLOWED,
    "filesystem.write": ToolPermission.ALLOWED,
    "terminal.execute": ToolPermission.ALLOWED,
    "git.operations": ToolPermission.ALLOWED,
    "project_management": ToolPermission.ALLOWED
}
