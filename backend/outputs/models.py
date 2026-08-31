from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum

class OutputContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class OutputType(str, Enum):
    TEXT = "text"
    STRUCTURED_DATA = "structured_data"
    DOCUMENT = "document"
    REPORT = "report"
    CODE = "code"
    CODE_PACKAGE = "code_package"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PRESENTATION = "presentation"
    DATASET = "dataset"
    ARCHIVE = "archive"
    ARTIFACT = "artifact"
    PACKAGE = "package"

class Cardinality(str, Enum):
    ONE = "one"
    MANY = "many"
    OPTIONAL = "optional"

class ArtifactPolicy(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    NONE = "none"

class DeliveryPolicy(str, Enum):
    USER_DOWNLOAD = "user_download"
    INLINE = "inline"
    REFERENCE = "reference"
    MULTI_ARTIFACT = "multi_artifact"

# ---------------------------------------------------------
# Output Contract Definition
# ---------------------------------------------------------
class OutputContract(BaseModel):
    id: Optional[str] = None
    output_contract_id: str
    name: str
    display_name: str
    description: str = ""
    domain: Optional[str] = None
    
    version: str = "1.0.0"
    status: OutputContractStatus = OutputContractStatus.DRAFT
    
    output_type: OutputType
    cardinality: Cardinality = Cardinality.ONE
    formats: List[str] = Field(default_factory=list) # e.g. ["mp4", "webm"]
    
    schema_reference: Optional[str] = None # Reference to a JSON schema if structured
    
    artifact_policy: ArtifactPolicy = ArtifactPolicy.REQUIRED
    delivery_policy: DeliveryPolicy = DeliveryPolicy.REFERENCE
    user_visible: bool = False
    is_final: bool = True
    
    metadata_requirements: Dict[str, Any] = Field(default_factory=dict) # e.g. {"resolution": "1080p", "fps": 30}
    content_requirements: List[str] = Field(default_factory=list) # e.g. ["must contain summary", "must contain call_to_action"]
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ---------------------------------------------------------
# Output Package Contract Definition (Multi-output)
# ---------------------------------------------------------
class OutputPackageContract(OutputContract):
    output_type: OutputType = OutputType.PACKAGE
    outputs: List[OutputContract] = Field(default_factory=list)
