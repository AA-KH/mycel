"""
Creative Development API Routes
Endpoints for interacting with the Creative Agent
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from organization.schemas import APIResponse
from teams.creative.agents.creative_agent import CreativeAgent

router = APIRouter()

class GenerateAssetRequest(BaseModel):
    task_description: str
    asset_type: str
    context: str = ""
    style_guidance: Optional[str] = None

class RefineAssetRequest(BaseModel):
    original_asset: str
    feedback: str
    asset_type: str = "image"

@router.post("/creative/generate", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def generate_creative_asset(request: GenerateAssetRequest):
    """Generate a creative asset (image, video, brand asset)."""
    try:
        agent = CreativeAgent()
        result = await agent.generate_asset(
            task_description=request.task_description,
            asset_type=request.asset_type,
            context=request.context,
            style_guidance=request.style_guidance
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Asset generation failed")
            )
        return APIResponse(data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Creative generation error: {str(e)}"
        )

@router.post("/creative/refine", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def refine_creative_asset(request: RefineAssetRequest):
    """Refine a creative asset."""
    try:
        agent = CreativeAgent()
        result = await agent.refine_asset(
            original_asset=request.original_asset,
            feedback=request.feedback,
            asset_type=request.asset_type
        )
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Asset refinement failed")
            )
        return APIResponse(data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Creative refinement error: {str(e)}"
        )
