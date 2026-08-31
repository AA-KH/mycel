"""
Output Delivery System — Domain Models (Phase 14)

Defines the entities that represent a packaged, user-facing delivery of
one or more Artifacts that satisfy an OutputContract.

Strict Boundaries:
- Delivery observes and packages Artifacts; it does NOT generate them.
- Delivery does NOT re-validate Quality Gates.
- Delivery does NOT modify TaskPlan or Evaluation results.
- Delivery does NOT store artifact binaries — only references and URLs.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class DeliveryStatus(str, Enum):
    PENDING    = "PENDING"
    PACKAGING  = "PACKAGING"
    READY      = "READY"
    DELIVERED  = "DELIVERED"
    EXPIRED    = "EXPIRED"
    FAILED     = "FAILED"


class DeliveryFormat(str, Enum):
    """
    How the artifacts are surfaced to the consumer.
    Mirrors OutputContract.DeliveryPolicy but is resolved at delivery time.
    """
    DIRECT_URL      = "DIRECT_URL"       # Single artifact, signed URL returned directly
    DOWNLOAD_BUNDLE = "DOWNLOAD_BUNDLE"  # Multiple artifacts zipped / grouped
    INLINE          = "INLINE"           # Small payload embedded in the response body
    REFERENCE       = "REFERENCE"        # Opaque storage reference (internal consumers)


class DeliveryItemStatus(str, Enum):
    PENDING  = "PENDING"
    READY    = "READY"
    EXPIRED  = "EXPIRED"
    FAILED   = "FAILED"


# ─────────────────────────────────────────────────────────────────────────────
# DeliveryItem — wraps a single resolved artifact
# ─────────────────────────────────────────────────────────────────────────────

class DeliveryItem(BaseModel):
    item_id: str = Field(default_factory=lambda: f"di_{uuid.uuid4().hex[:10]}")
    package_id: Optional[str] = None

    artifact_id: str
    artifact_type: str                       # "video", "image", "document", etc.
    mime_type: str
    filename: str
    size_bytes: int
    storage_provider: str                    # "cloudinary" | "gcs" | "local"

    # Resolved delivery URL (may be signed / time-limited)
    url: Optional[str] = None
    secure_url: Optional[str] = None
    signed: bool = False
    expires_at: Optional[datetime] = None

    status: DeliveryItemStatus = DeliveryItemStatus.PENDING
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# DeliveryPackage — aggregate root
# ─────────────────────────────────────────────────────────────────────────────

class DeliveryPackage(BaseModel):
    package_id: str = Field(default_factory=lambda: f"pkg_{uuid.uuid4().hex[:12]}")

    task_id: str
    organization_id: str = "mycel_global"
    output_contract_id: Optional[str] = None
    output_contract_version: Optional[str] = None

    format: DeliveryFormat = DeliveryFormat.DIRECT_URL
    status: DeliveryStatus = DeliveryStatus.PENDING

    items: List[DeliveryItem] = Field(default_factory=list)

    # When all items expire the package itself expires
    expires_at: Optional[datetime] = None

    # Delivery tracking
    packaged_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    delivery_count: int = 0               # How many times it has been fetched

    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_ready(self) -> bool:
        return self.status == DeliveryStatus.READY

    @property
    def is_expired(self) -> bool:
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return True
        return False


# ─────────────────────────────────────────────────────────────────────────────
# DeliveryResult — user-facing response model
# ─────────────────────────────────────────────────────────────────────────────

class DeliveryResult(BaseModel):
    package_id: str
    task_id: str
    status: DeliveryStatus
    format: DeliveryFormat
    items: List[DeliveryItem]
    expires_at: Optional[datetime] = None
    instructions: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# DeliveryRequest — input from the API layer
# ─────────────────────────────────────────────────────────────────────────────

class DeliveryRequest(BaseModel):
    task_id: str
    output_contract_id: Optional[str] = None
    format: DeliveryFormat = DeliveryFormat.DIRECT_URL
    signed_url_ttl_seconds: int = 3600     # Default 1 hour
    metadata: Dict[str, Any] = Field(default_factory=dict)
