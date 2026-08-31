from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid

class BuilderStage(str, Enum):
    COMPANY_INITIALIZATION = "COMPANY_INITIALIZATION"
    REQUIREMENTS_DISCOVERY = "REQUIREMENTS_DISCOVERY"
    FEASIBILITY_ANALYSIS = "FEASIBILITY_ANALYSIS"
    GROWTH_STRATEGY = "GROWTH_STRATEGY"
    BRAND_IDENTITY = "BRAND_IDENTITY"
    LOGO_CREATION = "LOGO_CREATION"
    POSTER_CREATION = "POSTER_CREATION"
    WEBSITE_CREATION = "WEBSITE_CREATION"
    PITCH_DECK_CREATION = "PITCH_DECK_CREATION"
    QUALITY_VALIDATION = "QUALITY_VALIDATION"

class PipelineStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"

class CompanyBuilderState(BaseModel):
    workflow_id: str = Field(default_factory=lambda: f"cb_{uuid.uuid4().hex[:10]}")
    company_id: str
    workspace_id: str
    
    current_stage: BuilderStage = BuilderStage.COMPANY_INITIALIZATION
    completed_stages: List[BuilderStage] = Field(default_factory=list)
    active_stages: List[BuilderStage] = Field(default_factory=list)
    pending_stages: List[BuilderStage] = Field(default_factory=lambda: [
        BuilderStage.REQUIREMENTS_DISCOVERY,
        BuilderStage.FEASIBILITY_ANALYSIS,
        BuilderStage.GROWTH_STRATEGY,
        BuilderStage.BRAND_IDENTITY,
        BuilderStage.LOGO_CREATION,
        BuilderStage.POSTER_CREATION,
        BuilderStage.WEBSITE_CREATION,
        BuilderStage.PITCH_DECK_CREATION,
        BuilderStage.QUALITY_VALIDATION
    ])
    failed_stages: List[BuilderStage] = Field(default_factory=list)
    
    status: PipelineStatus = PipelineStatus.PENDING
    
    # Store references to artifacts/memories generated during this workflow
    artifacts: Dict[str, str] = Field(default_factory=dict) # Stage -> ArtifactReference ID
    memories: List[str] = Field(default_factory=list) # List of Memory IDs
    tasks: List[str] = Field(default_factory=list) # List of Task IDs launched
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
