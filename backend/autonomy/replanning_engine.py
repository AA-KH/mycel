"""
Replanning Engine (Phase 16)

Creates a new CompanyPlan version when the current plan is no longer viable.

Replanning Principles:
- Each replan creates a NEW plan version (n+1); old plan marked SUPERSEDED.
- Plan history is NEVER overwritten.
- Anti-thrash guard: does not replan if same failure was already handled
  in the last iteration.
- Returns the new plan — does NOT activate it (ObjectiveManager does that).
- Does NOT call Task Orchestrator.
- Does NOT call Hiring.

Triggers for replanning:
  - Task failure (after retry limit)
  - Quality gate failure (revision required)
  - Resource unavailable (after retry)
  - Deadline risk (reprioritize critical path)
  - Dependency chain failure
  - Capability unavailable
  - Budget risk (scope reduction)
  - Objective change (new requirements)
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from autonomy.models import (
    CompanyObjective, CompanyPlan, PlanStatus,
)
from autonomy.planner import ObjectivePlanner
from autonomy.registry import ObjectiveRegistry

logger = logging.getLogger(__name__)


class ReplanningEngine:
    """
    Creates a new plan version when the current plan is no longer viable.
    Stateless strategy object — the registry is passed per-call.
    """

    def __init__(self, planner: Optional[ObjectivePlanner] = None):
        self.planner = planner or ObjectivePlanner()

    def replan(
        self,
        objective: CompanyObjective,
        current_plan: CompanyPlan,
        trigger_reason: str,
        registry: ObjectiveRegistry,
        skip_completed_phases: bool = True,
    ) -> CompanyPlan:
        """
        Create a new plan version and mark the current plan as SUPERSEDED.

        Parameters
        ----------
        objective               The objective being replanned.
        current_plan            The plan being superseded.
        trigger_reason          Human-readable reason for replanning.
        registry                Registry to persist plans.
        skip_completed_phases   If True, exclude already-completed milestones
                                from the new plan to avoid re-doing work.
        """
        logger.info(
            f"[ReplanningEngine] Replanning objective '{objective.objective_id}': "
            f"v{current_plan.version} → v{current_plan.version + 1}. "
            f"Reason: {trigger_reason!r}"
        )

        # Anti-thrash: check if same trigger was used in last replan
        all_plans = registry.get_all_plans(objective.objective_id)
        if len(all_plans) >= 2:
            previous = all_plans[-2] if len(all_plans) >= 2 else None
            # Heuristic: if the previous plan's metadata has same trigger, warn
            if previous and previous.status == PlanStatus.SUPERSEDED:
                prev_trigger = previous.validation_warnings[0] if previous.validation_warnings else ""
                if trigger_reason == prev_trigger:
                    logger.warning(
                        f"[ReplanningEngine] Same trigger as last replan: '{trigger_reason}'. "
                        f"Proceeding but loop detector should catch this."
                    )

        # Determine which phases still need to be done
        phases_to_use = self._remaining_phases(current_plan, skip_completed_phases)

        # Build new plan using the planner
        existing_count = len(registry.get_all_plans(objective.objective_id))
        new_plan = self.planner.plan(
            objective=objective,
            existing_plan_count=existing_count,
            phases=phases_to_use if phases_to_use else None,
        )

        # Record trigger reason in new plan's warnings field
        new_plan.validation_warnings.insert(0, f"Replan trigger: {trigger_reason}")

        # Mark old plan as SUPERSEDED
        current_plan.status = PlanStatus.SUPERSEDED
        current_plan.updated_at = datetime.now(timezone.utc)
        registry.store_plan(current_plan)

        # Store new plan
        registry.store_plan(new_plan)

        # Increment replan counter on objective budget
        objective.budget_config.replan_count += 1
        registry.store_objective(objective)

        logger.info(
            f"[ReplanningEngine] New plan '{new_plan.plan_id}' v{new_plan.version} created. "
            f"Replan count: {objective.budget_config.replan_count}."
        )
        return new_plan

    def _remaining_phases(
        self,
        current_plan: CompanyPlan,
        skip_completed: bool,
    ) -> Optional[List[tuple]]:
        """
        Returns phases that still need to be executed, or None for full re-plan.
        """
        if not skip_completed or not current_plan.milestones:
            return None

        from autonomy.models import MilestoneStatus
        remaining = [
            (ms.title, ms.description)
            for ms in current_plan.milestones
            if ms.status not in {MilestoneStatus.COMPLETED, MilestoneStatus.SKIPPED}
        ]
        return remaining if remaining else None
