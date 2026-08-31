from tools.registry.team_models import ToolImportance, AccessMode

rag_retrieval = {
    "tool_id": "rag_retrieval",
    "importance": ToolImportance.CORE,
    "required": True,
    "access_mode": AccessMode.READ
}
