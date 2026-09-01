from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from organization.schemas import APIResponse
import json

from teams.council.team_members.helena.agent import HelenaAgent
from teams.council.team_members.vikram.agent import VikramAgent
from teams.council.team_members.nisha.agent import NishaAgent
from teams.council.team_members.omar.agent import OmarAgent
from teams.council.team_members.sofia.agent import SofiaAgent

router = APIRouter()

class CouncilTaskRequest(BaseModel):
    task_description: str
    agent_name: str  # "helena", "vikram", "nisha", "omar", "sofia"

@router.post("/council/run", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def run_council_task(request: CouncilTaskRequest):
    agent_name = request.agent_name.lower()

    try:
        if agent_name == "helena":
            agent = HelenaAgent()
        elif agent_name == "vikram":
            agent = VikramAgent()
        elif agent_name == "nisha":
            agent = NishaAgent()
        elif agent_name == "omar":
            agent = OmarAgent()
        elif agent_name == "sofia":
            agent = SofiaAgent()
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid agent name. Must be one of: helena, vikram, nisha, omar, sofia."
            )

        result = await agent.run_task(task_description=request.task_description)

        return APIResponse(
            success=True,
            data={"result": result, "agent": agent_name}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
