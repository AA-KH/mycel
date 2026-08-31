"""
Completion Validator (Phase 16)

Verifies that a CompanyObjective truly satisfies all completion requirements
before it can be marked COMPLETED.

A task being technically COMPLETED is NOT sufficient.
ALL of the following must hold:
  1. All required milestones have completed status
  2. All required output types exist (artifact reference check)
  3. All quality gates passed
  4. All success criteria verifiable and met

"False completion" — tasks done but quality gate failed — must NOT mark
the objective as complete.

The validator does NOT:
  - Modify objective state (ObjectiveManager.complete() does that)
  - Create artifacts
  - Run evaluation
  - Call LLM
"""

import logging
from typing import Dict, List, Optional

from autonomy.models import (
    CompanyObjective, CompanyPlan, CompanyStateSnapshot,
    CompletionValidationResult, MilestoneStatus,
)

logger = logging.getLogger(__name__)


class ObjectiveCompletionValidator:
    """
    Validates all completion conditions before marking an objective COMPLETED.
    Stateless — safe to reuse across objectives.
    """

    def validate(
        self,
        objective: CompanyObjective,
        plan: Optional[CompanyPlan],
        snapshot: CompanyStateSnapshot,
        quality_results: Dict[str, bool],   # task_id → passed
        produced_output_types: List[str],   # Output types confirmed present
    ) -> CompletionValidationResult:
        missing: List[str] = []
        unmet: List[str] = []

        # 1. All milestones must be COMPLETED
        if not snapshot.milestone_progress:
            missing.append("No milestone progress available — cannot verify completion.")
        else:
            for mp in snapshot.milestone_progress:
                if mp.status != MilestoneStatus.COMPLETED:
                    missing.append(
                        f"Milestone '{mp.title}' is not completed (status={mp.status.value})."
                    )

        # 2. No tasks in failed state (quality gate failures count as failed)
        if snapshot.failed_task_count > 0:
            missing.append(
                f"{snapshot.failed_task_count} task(s) failed or failed quality gates — "
                f"objective cannot be marked complete."
            )

        # 3. Quality gates — all evaluated tasks must have passed
        failed_qg = [tid for tid, passed in quality_results.items() if not passed]
        if failed_qg:
            for tid in failed_qg:
                missing.append(f"Task '{tid}' failed quality gate — output not acceptable.")

        # 4. Required outputs (from plan and objective)
        if plan:
            for ms in plan.milestones:
                for req_output in ms.required_outputs:
                    if req_output not in produced_output_types:
                        missing.append(
                            f"Required output '{req_output}' (milestone: {ms.title}) "
                            f"has not been produced."
                        )

        # 5. Success criteria
        for sc in objective.success_criteria:
            if not sc.met:
                unmet.append(
                    f"Success criterion not met: '{sc.description}' "
                    f"(method={sc.verification_method})"
                )

        complete = len(missing) == 0 and len(unmet) == 0
        reason = (
            "All completion conditions satisfied."
            if complete
            else f"{len(missing)} missing requirements, {len(unmet)} unmet criteria."
        )

        if not complete:
            logger.info(
                f"[CompletionValidator] Objective '{objective.objective_id}' NOT complete: "
                f"{missing[:3]}{'...' if len(missing) > 3 else ''}"
            )

        return CompletionValidationResult(
            complete=complete,
            missing=missing,
            unmet_criteria=unmet,
            reason=reason,
        )
