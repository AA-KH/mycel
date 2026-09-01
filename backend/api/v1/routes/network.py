from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from organization.schemas import APIResponse

from teams.network.team_members.aanya.agent import AanyaAgent
from teams.network.team_members.dev.agent import DevAgent
from teams.network.team_members.kabir.agent import KabirAgent
from teams.network.team_members.tara.agent import TaraAgent

router = APIRouter()

class NetworkTaskRequest(BaseModel):
    task_description: str
    agent_name: str  # "aanya", "dev", "kabir", "tara"

@router.post("/network/run", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def run_network_task(request: NetworkTaskRequest):
    """Run a task with a specific Network team member."""
    agent_name = request.agent_name.lower()
    try:
        if agent_name == "aanya":
            agent = AanyaAgent()
        elif agent_name == "dev":
            agent = DevAgent()
        elif agent_name == "kabir":
            agent = KabirAgent()
        elif agent_name == "tara":
            agent = TaraAgent()
        else:
            raise HTTPException(status_code=400, detail="Invalid agent name. Must be one of aanya, dev, kabir, tara.")

        result = await agent.run_task(task_description=request.task_description)
        
        return APIResponse(data={"result": result, "agent": agent_name})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Network task error: {str(e)}"
        )
