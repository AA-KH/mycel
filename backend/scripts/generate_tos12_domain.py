import os
from pathlib import Path

BACKEND_DIR = Path("d:/Projects/agent-virtual-office/backend")
CAPABILITIES_DIR = BACKEND_DIR / "workforce" / "capabilities"

def ensure_dir(d):
    d.mkdir(parents=True, exist_ok=True)
    init_file = d / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

ensure_dir(CAPABILITIES_DIR)

models_content = """from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class CapabilityType(str, Enum):
    SKILL = "skill"
    TOOL = "tool"
    KNOWLEDGE = "knowledge"
    REASONING = "reasoning"
    PIPELINE = "pipeline"
    STAGE = "stage"
    OUTPUT = "output"
    QUALITY = "quality"

class CapabilityStatus(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    DENIED = "denied"
    INACTIVE = "inactive"

class CapabilitySourceType(str, Enum):
    TEAM_COMMON = "team_common"
    POSITION = "position"
    BASELINE = "baseline"
    MEMBER = "member"
    SPECIALIZATION = "specialization"
    SYSTEM = "system"

class CapabilityProvenance(BaseModel):
    capability_id: str
    capability_type: CapabilityType
    source_type: CapabilitySourceType
    source_id: str
    inherited_from: Optional[str] = None
    priority: int = 0
    reason: Optional[str] = None

class ResolvedCapability(BaseModel):
    capability_id: str
    capability_type: CapabilityType
    name: str
    source_type: CapabilitySourceType
    source_id: str
    proficiency: Optional[int] = None
    status: CapabilityStatus = CapabilityStatus.OPTIONAL
    provenance: CapabilityProvenance
    constraints: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CapabilityConflict(BaseModel):
    capability_id: str
    conflict_type: str
    message: str

class CapabilityGapType(str, Enum):
    MISSING = "missing"
    INSUFFICIENT_PROFICIENCY = "insufficient_proficiency"
    DENIED = "denied"
    INACTIVE = "inactive"
    INCOMPATIBLE = "incompatible"

class CapabilityGap(BaseModel):
    capability_id: str
    gap_type: CapabilityGapType
    required_proficiency: Optional[int] = None
    actual_proficiency: Optional[int] = None
    message: str

class CapabilitySnapshot(BaseModel):
    snapshot_id: str
    subject_type: str
    subject_id: str
    subject_version: str
    resolved_capabilities: List[ResolvedCapability]
    resolution_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolver_version: str = "1.0.0"
    hash: str

class CapabilityResolutionResult(BaseModel):
    subject_id: str
    subject_type: str
    capabilities: List[ResolvedCapability]
    provenance: List[CapabilityProvenance]
    conflicts: List[CapabilityConflict] = Field(default_factory=list)
    gaps: List[CapabilityGap] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
"""
(CAPABILITIES_DIR / "models.py").write_text(models_content, encoding="utf-8")

registry_content = """from typing import Optional, Dict
from workforce.capabilities.models import CapabilitySnapshot
import hashlib
import json

class CapabilitySnapshotRegistry:
    def __init__(self):
        self._snapshots: Dict[str, CapabilitySnapshot] = {}

    async def save_snapshot(self, snapshot: CapabilitySnapshot) -> str:
        self._snapshots[snapshot.snapshot_id] = snapshot
        return snapshot.snapshot_id

    async def get_snapshot(self, snapshot_id: str) -> Optional[CapabilitySnapshot]:
        return self._snapshots.get(snapshot_id)

class CapabilityComparator:
    def __init__(self):
        pass

    # Basic structure for future smart hiring integration
    def compare(self, required_capabilities, candidate_capabilities):
        pass
"""
(CAPABILITIES_DIR / "registry.py").write_text(registry_content, encoding="utf-8")

resolver_content = """from typing import List, Dict, Any, Optional
from workforce.capabilities.models import (
    CapabilityType, CapabilityStatus, CapabilitySourceType, CapabilityProvenance,
    ResolvedCapability, CapabilityResolutionResult, CapabilityConflict
)

class CapabilityResolver:
    def __init__(
        self,
        team_registry=None,
        position_registry=None,
        baseline_registry=None,
        member_registry=None
    ):
        self.team_registry = team_registry
        self.position_registry = position_registry
        self.baseline_registry = baseline_registry
        self.member_registry = member_registry

    def _resolve_layer(
        self, 
        base_capabilities: Dict[str, ResolvedCapability], 
        new_layer: Dict[str, Any], 
        source_type: CapabilitySourceType, 
        source_id: str, 
        inherited_from: Optional[str]
    ):
        for cap_id, cap_data in new_layer.items():
            new_status = cap_data.get("status", CapabilityStatus.OPTIONAL)
            new_prof = cap_data.get("proficiency", None)
            cap_type = cap_data.get("type", CapabilityType.SKILL)
            
            if cap_id in base_capabilities:
                existing = base_capabilities[cap_id]
                
                # DENY overrides ALLOW logic
                if existing.status == CapabilityStatus.DENIED or new_status == CapabilityStatus.DENIED:
                    existing.status = CapabilityStatus.DENIED
                
                # REQUIRED cannot downgrade to OPTIONAL logic
                elif existing.status == CapabilityStatus.REQUIRED and new_status == CapabilityStatus.OPTIONAL:
                    pass # Keep REQUIRED
                else:
                    existing.status = new_status

                # Child explicit proficiency overrides parent
                if new_prof is not None:
                    existing.proficiency = new_prof

                # Update provenance trail
                existing.provenance = CapabilityProvenance(
                    capability_id=cap_id,
                    capability_type=cap_type,
                    source_type=source_type,
                    source_id=source_id,
                    inherited_from=inherited_from,
                    reason=f"Updated by {source_type.value}"
                )
            else:
                base_capabilities[cap_id] = ResolvedCapability(
                    capability_id=cap_id,
                    capability_type=cap_type,
                    name=cap_id,
                    source_type=source_type,
                    source_id=source_id,
                    proficiency=new_prof,
                    status=new_status,
                    provenance=CapabilityProvenance(
                        capability_id=cap_id,
                        capability_type=cap_type,
                        source_type=source_type,
                        source_id=source_id,
                        inherited_from=inherited_from,
                        reason=f"Introduced by {source_type.value}"
                    )
                )

    async def resolve_team(self, team_id: str) -> CapabilityResolutionResult:
        caps = {}
        if self.team_registry:
            team = await self.team_registry.get_team(team_id)
            if team:
                layer = {}
                for s in getattr(team, 'common_skills', []):
                    # We might pass dicts for mock objects if they have statuses
                    if isinstance(s, dict):
                        layer[s['id']] = {"type": CapabilityType.SKILL, "status": s.get('status', CapabilityStatus.OPTIONAL), "proficiency": s.get('proficiency')}
                    else:
                        layer[s] = {"type": CapabilityType.SKILL, "status": CapabilityStatus.REQUIRED}
                for t in getattr(team, 'common_tools', []):
                    if isinstance(t, dict):
                        layer[t['id']] = {"type": CapabilityType.TOOL, "status": t.get('status', CapabilityStatus.OPTIONAL)}
                    else:
                        layer[t] = {"type": CapabilityType.TOOL, "status": CapabilityStatus.REQUIRED}
                
                self._resolve_layer(caps, layer, CapabilitySourceType.TEAM_COMMON, team_id, None)

        return CapabilityResolutionResult(
            subject_id=team_id,
            subject_type="team",
            capabilities=list(caps.values()),
            provenance=[c.provenance for c in caps.values()]
        )

    async def resolve_position(self, position_id: str) -> CapabilityResolutionResult:
        caps = {}
        team_id = None
        if self.position_registry:
            pos = await self.position_registry.get(position_id)
            if pos:
                team_id = pos.team_id
                # 1. Resolve Team
                team_result = await self.resolve_team(team_id)
                for c in team_result.capabilities:
                    caps[c.capability_id] = c
                
                # 2. Resolve Position
                layer = {}
                for req_skill in getattr(pos, 'required_skills', []):
                    # Some mock objects may be passed, handle them gracefully
                    if isinstance(req_skill, dict):
                        layer[req_skill['id']] = {"type": CapabilityType.SKILL, "proficiency": req_skill.get('proficiency'), "status": req_skill.get('status', CapabilityStatus.REQUIRED)}
                    else:
                        layer[req_skill.skill_id] = {"type": CapabilityType.SKILL, "proficiency": req_skill.minimum_proficiency, "status": CapabilityStatus.REQUIRED}
                
                for t in getattr(pos, 'required_tools', []):
                    if isinstance(t, dict):
                        layer[t['id']] = {"type": CapabilityType.TOOL, "status": t.get('status', CapabilityStatus.REQUIRED)}
                    else:
                        layer[t] = {"type": CapabilityType.TOOL, "status": CapabilityStatus.REQUIRED}

                self._resolve_layer(caps, layer, CapabilitySourceType.POSITION, position_id, team_id)

        return CapabilityResolutionResult(
            subject_id=position_id,
            subject_type="position",
            capabilities=list(caps.values()),
            provenance=[c.provenance for c in caps.values()]
        )

    async def resolve_baseline_member(self, baseline_member_id: str) -> CapabilityResolutionResult:
        caps = {}
        pos_id = None
        if self.baseline_registry:
            baseline = await self.baseline_registry.get(baseline_member_id)
            if baseline:
                pos_id = baseline.position_id
                
                # 1. Resolve Position
                pos_result = await self.resolve_position(pos_id)
                for c in pos_result.capabilities:
                    caps[c.capability_id] = c
                
                # 2. Resolve Baseline (additions)
                layer = {}
                for skill_id, skill_data in baseline.skills.items():
                    layer[skill_id] = {"type": CapabilityType.SKILL, "proficiency": skill_data.level, "status": CapabilityStatus.REQUIRED}
                for tool in baseline.tools:
                    layer[tool] = {"type": CapabilityType.TOOL, "status": CapabilityStatus.REQUIRED}

                self._resolve_layer(caps, layer, CapabilitySourceType.BASELINE, baseline_member_id, pos_id)

        return CapabilityResolutionResult(
            subject_id=baseline_member_id,
            subject_type="baseline",
            capabilities=list(caps.values()),
            provenance=[c.provenance for c in caps.values()]
        )

    async def resolve_member(self, member_id: str) -> CapabilityResolutionResult:
        caps = {}
        baseline_id = None
        if self.member_registry:
            member = await self.member_registry.get(member_id)
            if member:
                baseline_id = member.baseline_member_id
                
                # 1. Resolve Baseline
                if baseline_id:
                    baseline_result = await self.resolve_baseline_member(baseline_id)
                    for c in baseline_result.capabilities:
                        caps[c.capability_id] = c
                
                # 2. Resolve Member Direct Specialization
                layer = {}
                for s in getattr(member, 'specialization_skills', []):
                    layer[s['id']] = {"type": CapabilityType.SKILL, "proficiency": s.get('proficiency'), "status": s.get('status', CapabilityStatus.OPTIONAL)}
                for t in getattr(member, 'specialization_tools', []):
                    layer[t['id']] = {"type": CapabilityType.TOOL, "status": t.get('status', CapabilityStatus.OPTIONAL)}

                self._resolve_layer(caps, layer, CapabilitySourceType.SPECIALIZATION, member_id, baseline_id)

        return CapabilityResolutionResult(
            subject_id=member_id,
            subject_type="member",
            capabilities=list(caps.values()),
            provenance=[c.provenance for c in caps.values()]
        )
"""
(CAPABILITIES_DIR / "resolver.py").write_text(resolver_content, encoding="utf-8")

print("Generated capability domain models and resolver.")
