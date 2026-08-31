"""
Real Estate Domain — Production Models

Covers:
- PropertyRecord: full field set from the master spec
- CustomerContext: Kaushal-style lead data, keyed by customer_id
- IngestionJob: dataset versioning
- ConversationState: persistent in-memory state store
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# Intent Taxonomy
# ─────────────────────────────────────────────────────────────────────────────

class RealEstateIntent(str, Enum):
    PROPERTY_SEARCH = "PROPERTY_SEARCH"
    PROPERTY_RECOMMENDATION = "PROPERTY_RECOMMENDATION"
    PROPERTY_INVESTMENT_ANALYSIS = "PROPERTY_INVESTMENT_ANALYSIS"
    PROPERTY_LEGAL_QUERY = "PROPERTY_LEGAL_QUERY"
    PROPERTY_COMPARISON = "PROPERTY_COMPARISON"
    GENERAL_QUERY = "GENERAL_QUERY"


# ─────────────────────────────────────────────────────────────────────────────
# Property Model
# ─────────────────────────────────────────────────────────────────────────────

class PropertyRecord(BaseModel):
    property_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Property"
    property_type: str = "Apartment"
    bhk: Optional[int] = None
    area_sqft: Optional[float] = None
    price: Optional[float] = None
    location: Optional[str] = None
    city: Optional[str] = None
    locality: Optional[str] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    age: Optional[int] = None               # years since construction
    parking: Optional[int] = None           # number of parking spots
    amenities: List[str] = Field(default_factory=list)
    developer: Optional[str] = None
    availability: Optional[str] = None
    rental_yield: Optional[float] = None    # percentage e.g. 4.5
    historical_price: Optional[float] = None
    demand_score: Optional[float] = None    # 0-100
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    match_score: Optional[float] = None     # set at query time
    embedding: Optional[List[float]] = None # Vector embedding for semantic search


# ─────────────────────────────────────────────────────────────────────────────
# Customer / Lead Model
# ─────────────────────────────────────────────────────────────────────────────

class CustomerRequirements(BaseModel):
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    bhk: Optional[int] = None
    location: Optional[str] = None
    property_type: Optional[str] = None
    purpose: Optional[str] = None           # "family", "investment", "rental"
    investment_interest: bool = False
    preferred_floor: Optional[int] = None
    amenities_required: List[str] = Field(default_factory=list)


class CustomerContext(BaseModel):
    customer_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    lead_status: str = "warm"               # cold / warm / hot / converted
    previous_interactions: int = 0
    requirements: CustomerRequirements = Field(default_factory=CustomerRequirements)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# Dataset Versioning
# ─────────────────────────────────────────────────────────────────────────────

class IngestionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class IngestionJob(BaseModel):
    dataset_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    filename: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: IngestionStatus = IngestionStatus.PENDING
    row_count: int = 0
    rows_failed: int = 0
    schema_fields: List[str] = Field(default_factory=list)
    source: str = "xlsx_upload"
    error_detail: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Conversation State — in-memory store keyed by conversation_id
# ─────────────────────────────────────────────────────────────────────────────

class ConversationState(BaseModel):
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    language: str = "en"
    intent: Optional[RealEstateIntent] = None
    requirements: Dict[str, Any] = Field(default_factory=dict)
    active_task: Optional[str] = None
    active_team: Optional[str] = None
    active_member: Optional[str] = None
    current_stage: Optional[str] = None
    last_question: Optional[str] = None
    last_response: Optional[str] = None
    current_entities: List[str] = Field(default_factory=list)
    history: List[Dict[str, str]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# In-memory conversation state store — keyed by conversation_id
# In production this would be backed by Redis
_conversation_store: Dict[str, ConversationState] = {}


def get_or_create_conversation(conversation_id: str, customer_id: str) -> ConversationState:
    if conversation_id not in _conversation_store:
        _conversation_store[conversation_id] = ConversationState(
            conversation_id=conversation_id,
            customer_id=customer_id
        )
    return _conversation_store[conversation_id]


def update_conversation(state: ConversationState) -> None:
    state.updated_at = datetime.now(timezone.utc)
    _conversation_store[state.conversation_id] = state
