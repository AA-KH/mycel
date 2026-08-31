"""
Event Schemas for Mycel.
Standardized event envelopes and structures for all domain events.
"""

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


def generate_event_id() -> str:
    return str(uuid.uuid4())


class EventEnvelope(BaseModel):
    """
    Standard event envelope for all system events.
    """
    event_id: str = Field(default_factory=generate_event_id)
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    company_id: Optional[str] = None
    task_id: Optional[str] = None
    actor_id: Optional[str] = None
    correlation_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
