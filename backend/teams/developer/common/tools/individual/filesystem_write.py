from tools.registry.team_models import ToolImportance, AccessMode

filesystem_write = {
    "tool_id": "filesystem.write",
    "importance": ToolImportance.CORE,
    "required": True,
    "access_mode": AccessMode.WRITE
}
