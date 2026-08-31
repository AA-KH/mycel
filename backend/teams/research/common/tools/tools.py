from tools.registry.team_models import ToolImportance, AccessMode

RESEARCH_TOOLS = [
    {
        "tool_id": "web.search",
        "importance": ToolImportance.CORE,
        "required": True,
        "access_mode": AccessMode.READ
    },
    {
        "tool_id": "browser.open",
        "importance": ToolImportance.CORE,
        "required": True,
        "access_mode": AccessMode.READ
    },
    {
        "tool_id": "web.scrape",
        "importance": ToolImportance.CORE,
        "required": True,
        "access_mode": AccessMode.READ
    }
]
