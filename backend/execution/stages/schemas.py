from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from .models import (
    StageDefinitionStatus, StageCategory, StageInputContract,
    StageRequirementContract, StageValidationContract, StageFailurePolicy,
    StagePrecondition, StagePostcondition
)

class StageDefinitionCreate(BaseModel):
    stage_definition_id: str
    name: str
    display_name: str
    description: str
    purpose: str
    domain: str
    category: StageCategory
    input_contract: StageInputContract
    requirement_contract: StageRequirementContract
    validation_contract: Optional[StageValidationContract] = None
    failure_policy: Optional[StageFailurePolicy] = None
    preconditions: List[StagePrecondition] = []
    postconditions: List[StagePostcondition] = []

class StageRequirementContractResponse(BaseModel):
    skills: List[Any]
    tools: List[Any]
    knowledge: Any
    reasoning: Any
    output_contract_id: Optional[str] = None

class StageDefinitionResponse(BaseModel):
    id: str
    stage_definition_id: str
    name: str
    display_name: str
    description: str
    purpose: str
    domain: str
    category: StageCategory
    version: str
    status: StageDefinitionStatus
    input_contract: StageInputContract
    requirement_contract: StageRequirementContract
    validation_contract: StageValidationContract
    failure_policy: StageFailurePolicy
    preconditions: List[StagePrecondition]
    postconditions: List[StagePostcondition]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
