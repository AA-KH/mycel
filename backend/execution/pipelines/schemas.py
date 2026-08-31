from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from .models import (
    PipelineStatus, PipelineInputContract, PipelineStage
)

class TeamPipelineCreate(BaseModel):
    pipeline_id: str
    name: str
    display_name: str
    description: str
    input_contract: PipelineInputContract
    output_contract_id: Optional[str] = None
    stages: List[PipelineStage]

class TeamPipelineResponse(BaseModel):
    id: str
    pipeline_id: str
    team_id: str
    name: str
    display_name: str
    description: str
    version: str
    status: PipelineStatus
    input_contract: PipelineInputContract
    output_contract_id: Optional[str] = None
    stages: List[PipelineStage]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
