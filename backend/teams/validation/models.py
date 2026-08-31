from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class TeamReadiness(str, Enum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    NOT_READY = "NOT_READY"

class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: str
    path: str
    source: str = "validator"

class TeamValidationResult(BaseModel):
    team_id: str
    valid: bool = False
    readiness: TeamReadiness = TeamReadiness.NOT_READY
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    checks: int = 0
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeamValidationSummary(BaseModel):
    total_teams: int = 0
    valid_teams: int = 0
    invalid_teams: int = 0
    ready_teams: int = 0
    ready_with_warnings_teams: int = 0
    not_ready_teams: int = 0
    warnings: int = 0
    errors: int = 0
    results: List[TeamValidationResult] = Field(default_factory=list)
