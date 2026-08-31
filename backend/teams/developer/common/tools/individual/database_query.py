from tools.registry.team_models import ToolImportance, AccessMode

database_query = {
    "tool_id": "database.query",
    "importance": ToolImportance.SUPPORTING,
    "required": True,
    "access_mode": AccessMode.READ
}
