"""
Talent Market — Domain Models (Phase 15)

The Talent Market is a discovery layer over the Mycel workforce.
It surfaces who is available, what they can do, and how well they match
a set of capability requirements. It does NOT make hiring decisions.

Architectural Invariants
------------------------
- Talent Market is discovery.  Hiring is selection.
- TalentProfile is a projection; Employee is the source of truth.
- No LLM is used for basic matching.
- Candidate ranking is query-specific, never a global leaderboard.
- Missing data is NOT_EVALUATED, not 0.
- Talent Market never hires, assigns, creates Agents, grants Tools,
  activates Upskills, or changes Team membership.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class TalentAvailability(str, Enum):
    AVAILABLE   = "AVAILABLE"
    LIMITED     = "LIMITED"
    BUSY        = "BUSY"
    OFFLINE     = "OFFLINE"
    UNAVAILABLE = "UNAVAILABLE"


class MatchStatus(str, Enum):
    MATCH         = "MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    NO_MATCH      = "NO_MATCH"
    NOT_EVALUATED = "NOT_EVALUATED"


# ─────────────────────────────────────────────────────────────────────────────
# Search Request Components
# ─────────────────────────────────────────────────────────────────────────────

class SkillRequirement(BaseModel):
    skill_id: str
    minimum_proficiency: int = Field(ge=0, le=100, default=0)
    required: bool = True
    weight: float = Field(ge=0.0, le=1.0, default=1.0)


class CapabilityRequirement(BaseModel):
    capability_id: str
    required: bool = True


class ToolRequirement(BaseModel):
    tool_id: str
    required: bool = True


class TalentSearchRequest(BaseModel):
    """
    Structured request to discover candidates from the talent pool.
    All fields are optional; absent fields are ignored during filtering.
    """
    required_skills: List[SkillRequirement] = Field(default_factory=list)
    required_capabilities: List[CapabilityRequirement] = Field(default_factory=list)
    required_tools: List[ToolRequirement] = Field(default_factory=list)
    required_outputs: List[str] = Field(default_factory=list)   # e.g. ["video", "image"]

    # Preferred (soft constraints — affect score, not eligibility)
    preferred_skills: List[SkillRequirement] = Field(default_factory=list)

    # Structural filters
    team_id: Optional[str] = None          # Restrict to specific team
    position_id: Optional[str] = None      # Restrict / prefer specific position

    # Availability / workload filters
    availability_required: Optional[TalentAvailability] = None
    max_workload: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Exclusions
    exclude_employee_ids: List[str] = Field(default_factory=list)

    # Pagination / result bounding
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    # Scoring weight overrides (optional; service uses defaults if absent)
    score_weights: Optional[Dict[str, float]] = None


# ─────────────────────────────────────────────────────────────────────────────
# Talent Capability Snapshot — Derived Projection per Employee
# ─────────────────────────────────────────────────────────────────────────────

class TalentCapabilitySnapshot(BaseModel):
    """
    A derived, searchable projection of an Employee's effective capabilities.
    Built from: Employee skills + authorized tools + active upskills + Team membership.
    NOT the source of truth — snapshot_version tracks freshness.
    """
    snapshot_id: str = Field(default_factory=lambda: f"snap_{uuid.uuid4().hex[:10]}")
    employee_id: str
    team_id: str
    position_id: str

    # Effective skill proficiency map  { skill_id: proficiency_0_100 }
    skills: Dict[str, int] = Field(default_factory=dict)

    # Only tools where permission == ALLOWED
    authorized_tools: List[str] = Field(default_factory=list)

    # Effective capability IDs (from Team + Position + Upskills)
    capabilities: List[str] = Field(default_factory=list)

    # Active upskill capability IDs
    upskill_capabilities: List[str] = Field(default_factory=list)

    # Supported output types
    outputs: List[str] = Field(default_factory=list)

    # Derived availability
    availability: TalentAvailability = TalentAvailability.OFFLINE

    # Normalized workload  0.0 (idle) → 1.0 (fully occupied)
    workload: Optional[float] = None

    # Performance signals (from PerformanceSummary — already aggregated)
    overall_performance: Optional[float] = None   # 0 – 100
    tasks_completed: int = 0

    # Freshness metadata
    snapshot_version: int = 1
    is_stale: bool = False
    built_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# Talent Profile — User-Facing Projection
# ─────────────────────────────────────────────────────────────────────────────

class TalentProfile(BaseModel):
    """
    Public-facing projection of an Employee for discovery purposes.
    Does NOT expose private memory, internal evaluation details, or PII.
    """
    employee_id: str
    display_name: str
    team_id: str
    position_id: str
    specialization: str
    experience_level: str

    # Capability signals
    skills: Dict[str, int] = Field(default_factory=dict)       # skill_id → proficiency
    authorized_tools: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    upskill_capabilities: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)

    # Availability
    availability: TalentAvailability = TalentAvailability.OFFLINE
    workload: Optional[float] = None

    # Evaluation signals (only approved aggregate metrics — no raw details)
    overall_performance: Optional[float] = None
    tasks_completed: int = 0

    snapshot_version: int = 1


# ─────────────────────────────────────────────────────────────────────────────
# Match Breakdown — Per-Signal Match Explanation
# ─────────────────────────────────────────────────────────────────────────────

class DimensionResult(BaseModel):
    score: Optional[float] = None          # 0.0 – 1.0 or None if NOT_EVALUATED
    status: MatchStatus = MatchStatus.NOT_EVALUATED
    matched: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    detail: str = ""


class CandidateMatchBreakdown(BaseModel):
    skills: DimensionResult = Field(default_factory=DimensionResult)
    tools: DimensionResult = Field(default_factory=DimensionResult)
    capabilities: DimensionResult = Field(default_factory=DimensionResult)
    outputs: DimensionResult = Field(default_factory=DimensionResult)
    position: DimensionResult = Field(default_factory=DimensionResult)
    availability: DimensionResult = Field(default_factory=DimensionResult)
    workload: DimensionResult = Field(default_factory=DimensionResult)
    evaluation: DimensionResult = Field(default_factory=DimensionResult)


# ─────────────────────────────────────────────────────────────────────────────
# Candidate Reference — Handed off to Hiring
# ─────────────────────────────────────────────────────────────────────────────

class CandidateReference(BaseModel):
    """
    Lightweight reference returned by Talent Market to the Hiring system.
    Hiring must revalidate before making a final selection.
    """
    employee_id: str
    team_id: str
    position_id: str
    display_name: str
    availability: TalentAvailability

    match_score: float = Field(ge=0.0, le=1.0)
    match_breakdown: CandidateMatchBreakdown

    snapshot_version: int = 1
    snapshot_built_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Search Result
# ─────────────────────────────────────────────────────────────────────────────

class TalentSearchResult(BaseModel):
    items: List[CandidateReference] = Field(default_factory=list)
    total_eligible: int = 0
    total_matched: int = 0
    limit: int = 20
    offset: int = 0
    has_more: bool = False
    search_id: str = Field(default_factory=lambda: f"srch_{uuid.uuid4().hex[:8]}")
    searched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
