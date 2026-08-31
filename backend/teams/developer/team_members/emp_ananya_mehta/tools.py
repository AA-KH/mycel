from workforce.employees.models import ToolPermission

tools = [
    "filesystem.read",
    "filesystem.write",
    "browser.devtools",
    "design.tools",
    "git.operations"
]

permissions = {
    "filesystem.read": ToolPermission.ALLOWED,
    "filesystem.write": ToolPermission.ALLOWED,
    "browser.devtools": ToolPermission.ALLOWED,
    "design.tools": ToolPermission.ALLOWED,
    "git.operations": ToolPermission.ALLOWED
}
