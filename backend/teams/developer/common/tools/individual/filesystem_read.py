from tools.registry.team_models import ToolImportance, AccessMode

filesystem_read = {
    "tool_id": "filesystem.read",
    "importance": ToolImportance.CORE,
    "required": True,
    "access_mode": AccessMode.READ
}
