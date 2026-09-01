"""
Intelligence Team API Routes
Endpoints for interacting with the Intelligence Agents
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from organization.schemas import APIResponse

from teams.intelligence.team_members.mira.agent import MiraAgent
from teams.intelligence.team_members.ravi.agent import RaviAgent
from teams.intelligence.team_members.anika.agent import AnikaAgent
from teams.intelligence.team_members.noor.agent import NoorAgent

router = APIRouter()

class IntelligenceTaskRequest(BaseModel):
    task_description: str
    agent_name: str  # e.g., "mira", "ravi", "anika", "noor"

@router.post("/intelligence/run", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def run_intelligence_task(request: IntelligenceTaskRequest):
    """Run a task with a specific Intelligence team member."""
    agent_name = request.agent_name.lower()
    try:
        if agent_name == "mira":
            agent = MiraAgent()
        elif agent_name == "ravi":
            agent = RaviAgent()
        elif agent_name == "anika":
            agent = AnikaAgent()
        elif agent_name == "noor":
            agent = NoorAgent()
        else:
            raise HTTPException(status_code=400, detail="Invalid agent name. Must be one of mira, ravi, anika, noor.")

        result = await agent.run_task(task_description=request.task_description)
        
        return APIResponse(data={"result": result, "agent": agent_name})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intelligence task error: {str(e)}"
        )
