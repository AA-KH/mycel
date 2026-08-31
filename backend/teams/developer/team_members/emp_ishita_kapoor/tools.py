from workforce.employees.models import ToolPermission

tools = [
    "filesystem.read",
    "filesystem.write",
    "terminal.execute",
    "docker.operations",
    "kubernetes.operations",
    "cloud.cli",
    "git.operations"
]

permissions = {
    "filesystem.read": ToolPermission.ALLOWED,
    "filesystem.write": ToolPermission.ALLOWED,
    "terminal.execute": ToolPermission.ALLOWED,
    "docker.operations": ToolPermission.ALLOWED,
    "kubernetes.operations": ToolPermission.ALLOWED,
    "cloud.cli": ToolPermission.ALLOWED,
    "git.operations": ToolPermission.ALLOWED
}
