from typing import List, Dict, Any, Optional
from workforce.capabilities.models import (
    CapabilityType, CapabilityStatus, CapabilitySourceType, CapabilityProvenance,
    ResolvedCapability, CapabilityResolutionResult, CapabilityConflict
)

class CapabilityResolver:
    def __init__(
        self,
        team_registry=None,
        position_registry=None,
        member_registry=None,
        skill_registry=None,
        tool_registry=None
    ):
        self.team_registry = team_registry
        self.position_registry = position_registry
        self.member_registry = member_registry
        self.skill_registry = skill_registry
        self.tool_registry = tool_registry

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

    async def resolve_member(self, member_id: str) -> CapabilityResolutionResult:
        caps = {}
        pos_id = None
        if self.member_registry:
            member = await self.member_registry.get(member_id)
            if member:
                pos_id = member.position_id
                
                # 1. Resolve Position (which internally resolves Team Common)
                if pos_id:
                    pos_result = await self.resolve_position(pos_id)
                    for c in pos_result.capabilities:
                        caps[c.capability_id] = c
                
                # 2. Resolve Individual Member Capabilities
                layer = {}
                for skill_id, skill_data in member.skills.items():
                    layer[skill_id] = {"type": CapabilityType.SKILL, "proficiency": skill_data.level, "status": CapabilityStatus.REQUIRED}
                # No tools array in Member currently by default, but if there were:
                for tool in getattr(member, 'tools', []):
                    layer[tool] = {"type": CapabilityType.TOOL, "status": CapabilityStatus.REQUIRED}

                self._resolve_layer(caps, layer, CapabilitySourceType.MEMBER, member_id, pos_id)

                # 3. Resolve Member Direct Specialization
                spec_layer = {}
                for s in getattr(member, 'specialization_skills', []):
                    spec_layer[s['id']] = {"type": CapabilityType.SKILL, "proficiency": s.get('proficiency'), "status": s.get('status', CapabilityStatus.OPTIONAL)}
                for t in getattr(member, 'specialization_tools', []):
                    spec_layer[t['id']] = {"type": CapabilityType.TOOL, "status": t.get('status', CapabilityStatus.OPTIONAL)}

                self._resolve_layer(caps, spec_layer, CapabilitySourceType.SPECIALIZATION, member_id, member_id)

        return CapabilityResolutionResult(
            subject_id=member_id,
            subject_type="member",
            capabilities=list(caps.values()),
            provenance=[c.provenance for c in caps.values()]
        )
