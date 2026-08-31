from workforce.employees.models import ToolPermission

tools = [
    "filesystem.read",
    "filesystem.write",
    "test.frameworks",
    "automation.tools",
    "git.operations"
]

permissions = {
    "filesystem.read": ToolPermission.ALLOWED,
    "filesystem.write": ToolPermission.ALLOWED,
    "test.frameworks": ToolPermission.ALLOWED,
    "automation.tools": ToolPermission.ALLOWED,
    "git.operations": ToolPermission.ALLOWED
}
