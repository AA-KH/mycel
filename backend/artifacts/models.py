from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

class ArtifactStatus(str, Enum):
    CREATED = "created"
    UPLOADING = "uploading"
    VALIDATING = "validating"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"
    EXPIRED = "expired"

class ArtifactReference(BaseModel):
    """
    Lightweight reference returned to the LLM and AgentRuntime.
    Keeps heavy payloads out of the prompt window.
    """
    artifact_id: str
    type: str # "video", "image", "audio", "document", "text", "code"
    mime_type: str
    size_bytes: int
    storage: str # "cloudinary", "local", "gcs"
    url: Optional[str] = None
    secure_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Artifact(BaseModel):
    """
    Canonical database record representing an Artifact in Mycel.
    """
    artifact_id: str = Field(default_factory=lambda: f"art_{uuid.uuid4().hex[:12]}")
    company_id: str
    workspace_id: Optional[str] = None
    task_id: str
    execution_id: str
    employee_id: str
    
    type: str
    mime_type: str
    filename: str
    size_bytes: int
    checksum: Optional[str] = None
    
    status: ArtifactStatus = ArtifactStatus.CREATED
    
    storage_provider: str
    storage_key: str
    storage_public_id: Optional[str] = None
    url: Optional[str] = None
    secure_url: Optional[str] = None
    
    version: int = 1
    parent_artifact_id: Optional[str] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    visibility: str = "private" # "private", "company", "public"
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

class ArtifactValidationResult(BaseModel):
    artifact_id: str
    status: str # "passed", "failed"
    checks: List[Dict[str, str]] = Field(default_factory=list)
    reason: Optional[str] = None
