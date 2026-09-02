"""
Schemas for the per-operator onboarding setup record.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConstraintEntry(BaseModel):
    category: str = ""
    text: str = ""


class SetupPayload(BaseModel):
    """The nine-step wizard answers. Everything is optional so a partial
    save never blocks the operator from reaching mission control."""

    businessType: str = ""
    businessDescription: str = ""
    productName: str = ""
    productDescription: str = ""
    categories: str = ""
    brands: str = ""
    skuRange: str = ""
    customerTypes: str = ""
    supplySource: str = ""
    supplyCountries: str = ""
    operations: str = ""
    operationsDetails: str = ""
    customerScope: str = ""
    customerAreas: str = ""
    volume: str = ""
    demandPattern: str = ""
    peakSurge: str = ""
    timeline: str = ""
    targetDate: str = ""
    deadlineType: str = ""
    budgetTolerance: str = ""
    freightModes: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    constraints: list[ConstraintEntry] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    is_draft: bool = False


class SetupStatus(BaseModel):
    """Returned right after login so the client knows where to route."""

    has_setup: bool
    setup: dict[str, Any] | None = None
    completed_at: datetime | None = None
