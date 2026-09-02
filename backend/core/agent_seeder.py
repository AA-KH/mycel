import os
import importlib
import asyncio
from typing import List, Dict, Any
from pathlib import Path
import sys

# Ensure backend root is in PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.mongodb import mongodb_connection
from core.logger import logger

async def seed_agents():
    """
    Scrapes all agents from the teams directory and upserts them into MongoDB.
    """
    await mongodb_connection.connect()
    db = mongodb_connection.db
    agents_collection = db.agents
    
    teams_dir = backend_dir / "teams"
    hired_agents = []

    # Iterate through all teams
    for team_dir in teams_dir.iterdir():
        if not team_dir.is_dir() or team_dir.name.startswith("__"):
            continue
            
        members_dir = team_dir / "team_members"
        if not members_dir.exists():
            continue
            
        # Iterate through all members in the team
        for member_dir in members_dir.iterdir():
            if not member_dir.is_dir() or member_dir.name.startswith("__"):
                continue
                
            profile_path = member_dir / "profile.py"
            if profile_path.exists():
                try:
                    # Mock out models to avoid Pydantic validation errors during dynamic import
                    import sys
                    from unittest.mock import MagicMock
                    sys.modules['workforce'] = MagicMock()
                    sys.modules['workforce.employees'] = MagicMock()
                    sys.modules['workforce.employees.models'] = MagicMock()
                    
                    # Parse profile using regex to avoid Pydantic validation errors
                    with open(profile_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    import re
                    name_match = re.search(r'first_name\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                    role_match = re.search(r'(?:title|role)\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                    
                    if not name_match:
                        name_match = re.search(r'NAME\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                    if not role_match:
                        role_match = re.search(r'ROLE\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                        
                    name = name_match.group(1) if name_match else member_dir.name.capitalize()
                    role = role_match.group(1) if role_match else "Unknown Role"
                    
                    # Try to fetch prompt and tools via dynamic import
                    mandate = ""
                    tools_list = []
                    
                    module_base = f"teams.{team_dir.name}.team_members.{member_dir.name}"
                    
                    try:
                        # Ensure we mock profile imports if prompt imports from profile
                        import sys
                        from unittest.mock import MagicMock
                        sys.modules['workforce'] = MagicMock()
                        sys.modules['workforce.employees'] = MagicMock()
                        sys.modules['workforce.employees.models'] = MagicMock()
                        
                        prompt_mod = importlib.import_module(f"{module_base}.prompt")
                        mandate = getattr(prompt_mod, "SYSTEM_PROMPT", "")[:500] + "..." # Truncate for summary
                    except Exception:
                        pass
                        
                    try:
                        tools_mod = importlib.import_module(f"{module_base}.tools")
                        if hasattr(tools_mod, "get_tools"):
                            tools_raw = tools_mod.get_tools()
                            tools_list = [t.get("function", {}).get("name") for t in tools_raw if t.get("type") == "function"]
                    except Exception:
                        pass
                    
                    agent_id = f"{team_dir.name}_{member_dir.name}"
                    department = team_dir.name.capitalize()
                    
                    agent_data = {
                        "agent_id": agent_id,
                        "name": name,
                        "role": role,
                        "department": department,
                        "status": "AVAILABLE",
                        "skills": [f"Expertise in {role}"],
                        "tools": tools_list,
                        "mandate": mandate,
                        "cost_per_hour": 150 # Default cost
                    }
                    
                    # Upsert into MongoDB
                    await agents_collection.update_one(
                        {"agent_id": agent_id},
                        {"$set": agent_data},
                        upsert=True
                    )
                    
                    hired_agents.append(name)
                    logger.info(f"Seeded Agent: {name} ({role}) with {len(tools_list)} tools.")
                    
                except Exception as e:
                    logger.error(f"Failed to load agent {member_dir.name}: {e}")
                    
    logger.info(f"Agent seeding complete! Seeded {len(hired_agents)} agents.")
    await mongodb_connection.close()

if __name__ == "__main__":
    asyncio.run(seed_agents())
