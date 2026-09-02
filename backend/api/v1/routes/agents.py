from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from core.mongodb import mongodb_connection
from core.logger import logger

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_agents():
    """
    Returns a list of all available agents from MongoDB.
    Useful for the Frontend 'View All Team' directory.
    """
    try:
        db = mongodb_connection.db
        agents_cursor = db.agents.find({}, {"_id": 0})
        agents = await agents_cursor.to_list(length=100)
        return agents
    except Exception as e:
        logger.error(f"Failed to fetch agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch agents")

@router.get("/{agent_id}", response_model=Dict[str, Any])
async def get_agent(agent_id: str):
    """
    Fetch a specific agent by ID.
    """
    try:
        db = mongodb_connection.db
        agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0})
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch agent")
