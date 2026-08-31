from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class ArtifactReference(BaseModel):
    """
    Reference to a large or binary object to prevent LLM context bloat.
    """
    artifact_id: str
    type: str # "video", "image", "audio", "document", "dataset"
    mime_type: str
    size_bytes: int
    storage: str # "cloudinary", "local", "gcs"
    url: Optional[str] = None
    secure_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ToolDefinition(BaseModel):
    """
    Canonical definition of a Tool in the Mycel platform.
    """
    id: str
    name: str
    version: str = "1.0.0"
    category: str # "research", "browser", "filesystem", "media", "system"
    description: str
    
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    
    capabilities: List[str] = Field(default_factory=list)
    output_modalities: List[str] = Field(default_factory=list)
    artifact_types: List[str] = Field(default_factory=list)
    preview_types: List[str] = Field(default_factory=list)
    risk_level: str = "low" # "low", "medium", "high", "critical"
    
    requires_network: bool = False
    requires_approval: bool = False
    
    timeout_seconds: int = 30
    max_retries: int = 0
    idempotent: bool = False
    
    enabled: bool = True

# --- Tool Error Hierarchy ---

class ToolError(Exception):
    """Base class for all tool-related errors."""
    def __init__(self, message: str, tool_id: str):
        super().__init__(message)
        self.tool_id = tool_id

class ToolNotFoundError(ToolError):
    pass

class ToolPermissionDeniedError(ToolError):
    pass

class ToolApprovalRequiredError(ToolError):
    pass

class ToolValidationError(ToolError):
    pass

class ToolExecutionError(ToolError):
    pass

class ToolTimeoutError(ToolError):
    pass

class ToolUnavailableError(ToolError):
    pass
