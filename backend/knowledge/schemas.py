from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .models import (
    KnowledgeSpaceStatus, KnowledgeSourceType, TrustLevel, DocumentStatus
)

class KnowledgeSpaceCreate(BaseModel):
    team_id: str
    name: str
    description: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeSpaceResponse(BaseModel):
    id: str
    team_id: str
    name: str
    description: Optional[str]
    status: KnowledgeSpaceStatus
    configuration: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class KnowledgeSourceCreate(BaseModel):
    name: str
    type: KnowledgeSourceType
    uri: str
    description: Optional[str] = None
    trust_level: TrustLevel = TrustLevel.UNVERIFIED
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeSourceResponse(BaseModel):
    id: str
    knowledge_space_id: str
    name: str
    type: KnowledgeSourceType
    uri: str
    description: Optional[str]
    status: str
    trust_level: TrustLevel
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class KnowledgeDocumentResponse(BaseModel):
    id: str
    source_id: str
    knowledge_space_id: str
    title: str
    description: Optional[str]
    content_type: str
    version: str
    checksum: Optional[str]
    status: DocumentStatus
    metadata: Dict[str, Any]
    indexed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
