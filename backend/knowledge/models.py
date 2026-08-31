from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class KnowledgeSpaceStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"

class KnowledgeSourceType(str, Enum):
    DOCUMENT = "document"
    WEB_PAGE = "web_page"
    WEB_SITE = "web_site"
    DATABASE = "database"
    API = "api"
    DATASET = "dataset"
    CLOUD_STORAGE = "cloud_storage"
    UPLOADED_FILE = "uploaded_file"
    INTERNAL_DOCUMENT = "internal_document"

class TrustLevel(str, Enum):
    UNVERIFIED = "unverified"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    OFFICIAL = "official"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"


# ---------------------------------------------------------
# Core Domain Models
# ---------------------------------------------------------

class KnowledgeSpace(BaseModel):
    """
    A bounded context of knowledge belonging to a specific Team.
    """
    id: Optional[str] = None
    team_id: str
    name: str
    description: Optional[str] = None
    status: KnowledgeSpaceStatus = KnowledgeSpaceStatus.ACTIVE
    configuration: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeSource(BaseModel):
    """
    The conceptual origin of knowledge (e.g. a website, an uploaded file).
    """
    id: Optional[str] = None
    knowledge_space_id: str
    name: str
    type: KnowledgeSourceType
    uri: str  # URL, Cloudinary ID, File Path, etc.
    description: Optional[str] = None
    status: str = "active"
    trust_level: TrustLevel = TrustLevel.UNVERIFIED
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeDocument(BaseModel):
    """
    A logical document ingested from a KnowledgeSource.
    """
    id: Optional[str] = None
    source_id: str
    knowledge_space_id: str
    title: str
    description: Optional[str] = None
    content_type: str = "text/plain" # mime type
    version: str = "1.0"
    checksum: Optional[str] = None
    status: DocumentStatus = DocumentStatus.PENDING
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    indexed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeChunk(BaseModel):
    """
    An embeddable unit of text derived from a KnowledgeDocument.
    """
    id: Optional[str] = None
    document_id: str
    knowledge_space_id: str
    content: str
    position: int = 0
    token_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------
# Retrieval Contract Models
# ---------------------------------------------------------

class KnowledgeReference(BaseModel):
    """
    Lightweight reference object passed to the LLM.
    """
    knowledge_reference_id: str
    document_id: str
    chunk_id: str
    knowledge_space_id: str
    title: str
    source: str
    relevance_score: float
    citation_metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeContext(BaseModel):
    """
    The RAG context passed to the Reasoning Engine.
    """
    team_id: str
    query: str
    references: List[KnowledgeReference]
    retrieved_chunks: List[Dict[str, Any]] # e.g. {"chunk_id": "...", "content": "..."}
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
