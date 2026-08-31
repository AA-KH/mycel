"""
Developer API Routes
Endpoints for interacting with the Developer Agent
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel
from organization.schemas import APIResponse
from teams.developer.agents.developer_agent import DeveloperAgent

router = APIRouter()

class DevelopCodeRequest(BaseModel):
    task_description: str
    skill_type: str
    context: str = ""

@router.post("/developer/develop", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def develop_software_code(request: DevelopCodeRequest):
    """Generate software code using the Developer Agent."""
    try:
        agent = DeveloperAgent()
        result = await agent.develop_code(
            task_description=request.task_description,
            skill_type=request.skill_type,
            context=request.context
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Code development failed")
            )
        return APIResponse(data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code development error: {str(e)}"
        )
