from tools.registry.team_models import ToolImportance, AccessMode

CREATIVE_TOOLS = [
    {
        "tool_id": "ffmpeg",
        "importance": ToolImportance.CORE,
        "required": True,
        "access_mode": AccessMode.EXECUTE
    },
    {
        "tool_id": "cloudinary.upload",
        "importance": ToolImportance.SUPPORTING,
        "required": False,
        "access_mode": AccessMode.WRITE
    }
]
