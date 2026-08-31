"""
Talent Snapshot Builder (Phase 15)

Builds a TalentCapabilitySnapshot — a derived, searchable projection of
an Employee's effective capabilities — from authoritative Workforce data.

The builder:
- Normalizes skills from Employee.skills dict.
- Resolves AUTHORIZED tools from Employee.permissions (not just .tools list).
- Projects Employee.availability → TalentAvailability.
- Accepts optional upskill capability IDs (injected by caller).
- Accepts optional workload score (injected from task system).

The builder does NOT:
- Call LLM.
- Query Hiring.
- Modify Employee state.
- Contact Hugging Face.
- Read all Memory.
"""

import logging
from typing import List, Optional

from workforce.employees.models import Employee, EmployeeStatus, EmployeeAvailability, ToolPermission
from talent.models import TalentCapabilitySnapshot, TalentAvailability

logger = logging.getLogger(__name__)

# Map Employee availability → Talent availability
_AVAILABILITY_MAP = {
    EmployeeAvailability.AVAILABLE: TalentAvailability.AVAILABLE,
    EmployeeAvailability.BUSY: TalentAvailability.BUSY,
    EmployeeAvailability.OFFLINE: TalentAvailability.OFFLINE,
}


class TalentSnapshotBuilder:
    """
    Builds TalentCapabilitySnapshot from an Employee definition.
    Stateless — safe to reuse across requests.
    """

    def build(
        self,
        employee: Employee,
        upskill_capabilities: Optional[List[str]] = None,
        workload: Optional[float] = None,
        team_capabilities: Optional[List[str]] = None,
        version: int = 1,
    ) -> TalentCapabilitySnapshot:
        """
        Project an Employee into a TalentCapabilitySnapshot.

        Parameters
        ----------
        employee            The authoritative Employee definition.
        upskill_capabilities  Active Upskill capability IDs (injected by caller).
        workload            Normalized 0.0–1.0 workload (injected from task system).
        team_capabilities   Capability IDs contributed by Team/Position layer.
        version             Snapshot version number for staleness tracking.
        """
        # 1. Skills — normalize proficiency from SkillProficiency objects
        skills: dict = {}
        for skill_id, prof in (employee.skills or {}).items():
            # SkillProficiency has a .level attribute
            level = prof.level if hasattr(prof, "level") else int(prof)
            skills[skill_id] = level

        # 2. Authorized tools — ONLY where permission == ALLOWED
        authorized_tools: List[str] = []
        for tool_id in (employee.tools or []):
            perm = (employee.permissions or {}).get(tool_id)
            if perm == ToolPermission.ALLOWED:
                authorized_tools.append(tool_id)

        # 3. Capabilities — union of team_capabilities + upskill_capabilities
        upskills = list(upskill_capabilities or [])
        team_caps = list(team_capabilities or [])
        all_capabilities = list(set(team_caps + upskills))

        # 4. Availability mapping
        availability = _AVAILABILITY_MAP.get(
            employee.availability, TalentAvailability.UNAVAILABLE
        )

        # 5. Performance signals — already aggregated on Employee
        perf = employee.performance_summary
        overall_perf = perf.overall_score if perf else None
        tasks_done = perf.tasks_completed if perf else 0

        return TalentCapabilitySnapshot(
            employee_id=employee.employee_id,
            team_id=employee.team_id,
            position_id=employee.position_id,
            skills=skills,
            authorized_tools=authorized_tools,
            capabilities=all_capabilities,
            upskill_capabilities=upskills,
            outputs=list(employee.outputs or []),
            availability=availability,
            workload=workload,
            overall_performance=overall_perf,
            tasks_completed=tasks_done,
            snapshot_version=version,
            is_stale=False,
        )
