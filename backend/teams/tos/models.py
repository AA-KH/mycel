"""
Team Operating System — Integration Models (TOS 20)

These models provide a unified, read-only view over all TOS 0–19 subsystems.

Design invariants:
    - All fields contain IDs, references, and safe summaries only.
    - No secrets, credentials, API keys, raw knowledge, raw artifacts.
    - No hidden prompts or reasoning traces.
    - Nothing executes — this is contract-level metadata only.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# Readiness (TOS 20 extension — adds PARTIALLY_READY and DEGRADED)
# ─────────────────────────────────────────────────────────────────────────────

class TOSTeamReadiness(str, Enum):
    """
    TOS 20 readiness states (superset of TOS 17 TeamReadiness).

    NOT_READY:       Fundamental identity or configuration is broken.
    PARTIALLY_READY: Identity valid but ≥1 non-critical capability is missing.
    READY:           All components valid, no errors.
    DEGRADED:        Previously operational; a critical runtime dependency is
                     currently declared unavailable (not a config error).
    """
    NOT_READY = "NOT_READY"
    PARTIALLY_READY = "PARTIALLY_READY"
    READY = "READY"
    DEGRADED = "DEGRADED"


# ─────────────────────────────────────────────────────────────────────────────
# Per-component validation slice
# ─────────────────────────────────────────────────────────────────────────────

class TOSValidationComponent(BaseModel):
    """
    A lightweight validation result from a single subsystem.
    Aggregated by TOSTeamValidationReport.
    """
    component: str                          # e.g. "identity", "pipelines", "execution_contracts"
    status: str = "UNKNOWN"                 # "VALID", "INVALID", "WARNING", "SKIPPED"
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Unified validation report
# ─────────────────────────────────────────────────────────────────────────────

class TOSTeamValidationReport(BaseModel):
    """
    Aggregated validation report across all TOS subsystems for a team.
    Orchestrates existing validators — does NOT duplicate their logic.
    """
    team_id: str
    overall_valid: bool = False
    readiness: TOSTeamReadiness = TOSTeamReadiness.NOT_READY
    components: List[TOSValidationComponent] = Field(default_factory=list)
    total_errors: int = 0
    total_warnings: int = 0
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def add_component(self, component: TOSValidationComponent) -> None:
        self.components.append(component)
        self.total_errors += len(component.errors)
        self.total_warnings += len(component.warnings)


# ─────────────────────────────────────────────────────────────────────────────
# Capability view (derived — not a second source of truth)
# ─────────────────────────────────────────────────────────────────────────────

class TOSTeamCapabilityView(BaseModel):
    """
    Derived capability view for a team.
    Contains IDs/names only — sourced from TeamCapabilityProfile.
    """
    team_id: str
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    knowledge: List[str] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)
    pipelines: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    quality_requirements: List[str] = Field(default_factory=list)
    positions: List[str] = Field(default_factory=list)
    resolved: bool = False
    resolution_errors: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Contract map
# ─────────────────────────────────────────────────────────────────────────────

class TOSContractMap(BaseModel):
    """
    Team's contract ID references — no full contract objects.
    Execution contracts: how this team executes its own work.
    Collaboration contracts: how this team interacts with other teams.
    """
    team_id: str
    execution_contract_ids: List[str] = Field(default_factory=list)
    outgoing_collaboration_ids: List[str] = Field(default_factory=list)  # team provides
    incoming_collaboration_ids: List[str] = Field(default_factory=list)  # team requests


# ─────────────────────────────────────────────────────────────────────────────
# Health report
# ─────────────────────────────────────────────────────────────────────────────

class TOSComponentHealth(BaseModel):
    component: str
    healthy: bool = True
    issues: List[str] = Field(default_factory=list)


class TOSTeamHealthReport(BaseModel):
    """
    Lightweight health summary for a team.
    Calculated from validation + capability resolution results.
    Does NOT execute anything.
    """
    team_id: str
    status: str = "UNKNOWN"                 # "HEALTHY", "DEGRADED", "UNHEALTHY"
    readiness: TOSTeamReadiness = TOSTeamReadiness.NOT_READY
    components: List[TOSComponentHealth] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# Operating profile (human-readable derived view)
# ─────────────────────────────────────────────────────────────────────────────

class TOSTeamOperatingProfile(BaseModel):
    """
    Human-readable operational profile for a team.
    Derived on-demand from existing subsystems.
    Contains summaries and IDs only — not raw data.
    """
    team_id: str
    team_name: str = ""
    description: str = ""
    status: str = ""
    readiness: TOSTeamReadiness = TOSTeamReadiness.NOT_READY

    # Identity
    company_id: str = ""
    slug: str = ""

    # Capabilities (IDs/names)
    common_skills: List[str] = Field(default_factory=list)
    common_tools: List[str] = Field(default_factory=list)
    knowledge_spaces: List[str] = Field(default_factory=list)
    reasoning_profiles: List[str] = Field(default_factory=list)

    # Pipelines
    pipeline_ids: List[str] = Field(default_factory=list)

    # Outputs & quality
    output_contract_ids: List[str] = Field(default_factory=list)
    quality_gate_ids: List[str] = Field(default_factory=list)

    # Workforce
    position_ids: List[str] = Field(default_factory=list)
    member_count: int = 0

    # Contracts
    execution_contract_ids: List[str] = Field(default_factory=list)
    outgoing_collaboration_ids: List[str] = Field(default_factory=list)
    incoming_collaboration_ids: List[str] = Field(default_factory=list)
    collaborates_with: List[str] = Field(default_factory=list)  # team IDs

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# Team Operating System Snapshot (the primary integration artefact)
# ─────────────────────────────────────────────────────────────────────────────

class TOSTeamSnapshot(BaseModel):
    """
    Stable, lightweight snapshot of a team's complete operational state.

    Security invariants:
        - No API keys or credentials.
        - No private prompts or reasoning traces.
        - No raw knowledge documents.
        - No raw artifact binaries.
        - No personal employee data beyond IDs and names.

    Only IDs, references, counts, and safe summaries are included.
    """
    # Identity
    team_id: str
    team_name: str = ""
    company_id: str = ""
    slug: str = ""
    status: str = ""
    version: str = "1.0.0"

    # Readiness & validation
    readiness: TOSTeamReadiness = TOSTeamReadiness.NOT_READY
    validation_valid: bool = False
    validation_error_count: int = 0
    validation_warning_count: int = 0

    # Capabilities (IDs only)
    skill_ids: List[str] = Field(default_factory=list)
    tool_ids: List[str] = Field(default_factory=list)
    knowledge_ids: List[str] = Field(default_factory=list)
    reasoning_ids: List[str] = Field(default_factory=list)
    capability_resolved: bool = False

    # Pipelines (IDs only)
    pipeline_ids: List[str] = Field(default_factory=list)
    stage_ids: List[str] = Field(default_factory=list)

    # Quality & outputs (IDs only)
    quality_gate_ids: List[str] = Field(default_factory=list)
    output_contract_ids: List[str] = Field(default_factory=list)

    # Workforce (IDs only — no personal data)
    position_ids: List[str] = Field(default_factory=list)
    member_ids: List[str] = Field(default_factory=list)
    member_count: int = 0

    # Contracts (IDs only)
    execution_contract_ids: List[str] = Field(default_factory=list)
    outgoing_collaboration_ids: List[str] = Field(default_factory=list)
    incoming_collaboration_ids: List[str] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_ready(self) -> bool:
        return self.readiness == TOSTeamReadiness.READY

    @property
    def is_operational(self) -> bool:
        return self.readiness in (TOSTeamReadiness.READY, TOSTeamReadiness.PARTIALLY_READY)
