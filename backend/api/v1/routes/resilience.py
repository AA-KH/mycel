from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from organization.schemas import APIResponse
import json

from teams.resilience.team_members.zoya.agent import ZoyaAgent
from teams.resilience.team_members.vikram.agent import VikramAgent
from teams.resilience.team_members.ishaan.agent import IshaanAgent
from teams.resilience.team_members.leena.agent import LeenaAgent

router = APIRouter()

class ResilienceTaskRequest(BaseModel):
    task_description: str
    agent_name: str  # "zoya", "vikram", "ishaan", "leena"

@router.post("/resilience/run", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def run_resilience_task(request: ResilienceTaskRequest):
    agent_name = request.agent_name.lower()
    
    try:
        if agent_name == "zoya":
            agent = ZoyaAgent()
        elif agent_name == "vikram":
            agent = VikramAgent()
        elif agent_name == "ishaan":
            agent = IshaanAgent()
        elif agent_name == "leena":
            agent = LeenaAgent()
        else:
            raise HTTPException(status_code=400, detail="Invalid agent name. Must be one of zoya, vikram, ishaan, leena.")

        result = await agent.run_task(task_description=request.task_description)
        
        return APIResponse(
            success=True,
            data={"result": result, "agent": agent_name}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
