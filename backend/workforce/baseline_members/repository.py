from typing import List, Optional
from workforce.baseline_members.models import BaselineMember, BaselineStatus

class BaselineMemberRepository:
    def __init__(self):
        # In-memory storage for now, simulating MongoDB
        self._members = {}
        
    async def create(self, member: BaselineMember) -> BaselineMember:
        key = f"{member.baseline_member_id}_{member.baseline_version}"
        if key in self._members:
            raise ValueError(f"Baseline Member {key} already exists")
        self._members[key] = member
        return member

    async def get_by_baseline_id(self, baseline_member_id: str, version: Optional[str] = None) -> Optional[BaselineMember]:
        if version:
            return self._members.get(f"{baseline_member_id}_{version}")
        
        # Return the most recent/active version
        matches = [m for m in self._members.values() if m.baseline_member_id == baseline_member_id]
        if not matches:
            return None
            
        active = [m for m in matches if m.status == BaselineStatus.ACTIVE]
        return active[0] if active else matches[-1]

    async def get_by_team(self, team_id: str) -> List[BaselineMember]:
        return [m for m in self._members.values() if m.team_id == team_id and m.status == BaselineStatus.ACTIVE]
        
    async def get_by_position(self, position_id: str) -> List[BaselineMember]:
        return [m for m in self._members.values() if m.position_id == position_id and m.status == BaselineStatus.ACTIVE]

    async def get_all_active(self) -> List[BaselineMember]:
        return [m for m in self._members.values() if m.status == BaselineStatus.ACTIVE]

    async def find(self, query: dict, limit: int = 100) -> List[BaselineMember]:
        results = []
        for m in self._members.values():
            match = True
            for k, v in query.items():
                if "." in k:
                    # Simple nested dict check for tools/skills lists
                    field, subfield = k.split(".", 1)
                    val = getattr(m, field, None)
                    if isinstance(val, list) and v not in val:
                        match = False
                    elif isinstance(val, dict) and v not in val:
                        match = False
                else:
                    if getattr(m, k, None) != v:
                        match = False
            if match:
                results.append(m)
                if len(results) >= limit:
                    break
        return results
