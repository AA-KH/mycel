from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from .models import (
    OutputContractStatus, OutputType, Cardinality, 
    ArtifactPolicy, DeliveryPolicy, OutputContract
)

class OutputContractResponse(BaseModel):
    id: str
    output_contract_id: str
    name: str
    display_name: str
    description: str
    domain: Optional[str]
    version: str
    status: OutputContractStatus
    output_type: OutputType
    cardinality: Cardinality
    formats: List[str]
    schema_reference: Optional[str]
    artifact_policy: ArtifactPolicy
    delivery_policy: DeliveryPolicy
    user_visible: bool
    is_final: bool
    metadata_requirements: Dict[str, Any]
    content_requirements: List[str]
    created_at: datetime
    updated_at: datetime
