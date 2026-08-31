from tools.registry.team_models import ToolImportance, AccessMode

document_generation = {
    "tool_id": "document_generation",
    "importance": ToolImportance.CORE,
    "required": True,
    "access_mode": AccessMode.WRITE
}
