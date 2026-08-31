"""
Talent Candidate Filter (Phase 15)

Evaluates hard eligibility constraints.
A candidate that fails ANY required constraint is excluded from the pool
BEFORE any scoring occurs.

Filter checks (in order):
1.  Employee active status
2.  Availability requirement
3.  Workload cap
4.  Required skill proficiency
5.  Required tool authorization (checks authorized_tools, NOT raw tools list)
6.  Required capability presence
7.  Required output type support
8.  Team restriction
9.  Position restriction
10. Explicit exclusion list

The filter does NOT:
- Score candidates.
- Call LLM.
- Modify any state.
- Hire or assign.
"""

import logging
from typing import List, Tuple

from talent.models import (
    TalentCapabilitySnapshot, TalentSearchRequest, TalentAvailability
)

logger = logging.getLogger(__name__)

# Availability ordering — higher means less available
_AVAILABILITY_ORDER = {
    TalentAvailability.AVAILABLE:   0,
    TalentAvailability.LIMITED:     1,
    TalentAvailability.BUSY:        2,
    TalentAvailability.OFFLINE:     3,
    TalentAvailability.UNAVAILABLE: 4,
}


class TalentCandidateFilter:
    """
    Evaluates hard eligibility constraints against a TalentCapabilitySnapshot.
    Returns (is_eligible: bool, rejection_reasons: List[str]).
    """

    @classmethod
    def evaluate(
        cls,
        snapshot: TalentCapabilitySnapshot,
        request: TalentSearchRequest,
    ) -> Tuple[bool, List[str]]:
        reasons: List[str] = []

        # 1. Exclusion list
        if snapshot.employee_id in request.exclude_employee_ids:
            reasons.append("explicitly_excluded")
            return False, reasons

        # 2. Availability
        if request.availability_required is not None:
            required_level = _AVAILABILITY_ORDER.get(request.availability_required, 99)
            actual_level = _AVAILABILITY_ORDER.get(snapshot.availability, 99)
            if actual_level > required_level:
                reasons.append(
                    f"availability_mismatch:"
                    f"required={request.availability_required.value},"
                    f"actual={snapshot.availability.value}"
                )

        # 3. Workload cap
        if request.max_workload is not None:
            if snapshot.workload is None:
                # Workload unknown — treat as NOT_EVALUATED, do not reject
                pass
            elif snapshot.workload > request.max_workload:
                reasons.append(
                    f"workload_exceeded:actual={snapshot.workload:.2f},"
                    f"max={request.max_workload:.2f}"
                )

        # 4. Team restriction
        if request.team_id and snapshot.team_id != request.team_id:
            reasons.append(
                f"team_mismatch:required={request.team_id},"
                f"actual={snapshot.team_id}"
            )

        # 5. Position restriction
        if request.position_id and snapshot.position_id != request.position_id:
            reasons.append(
                f"position_mismatch:required={request.position_id},"
                f"actual={snapshot.position_id}"
            )

        # 6. Required skills — minimum proficiency gate
        for s_req in request.required_skills:
            if not s_req.required:
                continue
            actual_prof = snapshot.skills.get(s_req.skill_id, 0)
            if actual_prof < s_req.minimum_proficiency:
                reasons.append(
                    f"insufficient_skill:{s_req.skill_id}:"
                    f"required>={s_req.minimum_proficiency},actual={actual_prof}"
                )

        # 7. Required tools — MUST be in authorized_tools (not raw tool list)
        for t_req in request.required_tools:
            if not t_req.required:
                continue
            if t_req.tool_id not in snapshot.authorized_tools:
                reasons.append(f"tool_not_authorized:{t_req.tool_id}")

        # 8. Required capabilities
        all_caps = set(snapshot.capabilities) | set(snapshot.upskill_capabilities)
        for c_req in request.required_capabilities:
            if not c_req.required:
                continue
            if c_req.capability_id not in all_caps:
                reasons.append(f"missing_capability:{c_req.capability_id}")

        # 9. Required outputs
        for out_type in request.required_outputs:
            if out_type not in snapshot.outputs:
                reasons.append(f"unsupported_output:{out_type}")

        return len(reasons) == 0, reasons
