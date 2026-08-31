"""
Progress Tracker (Phase 16)

Computes objective progress as a bounded 0.0–1.0 score based on
meaningful work completion — NOT on:
  - Number of agent messages
  - Number of LLM calls
  - Number of tool invocations
  - Task technical completion without quality gate passage

Progress = weighted average of milestone completions.
A milestone is considered complete only when all its tasks have BOTH:
  (a) status = COMPLETED
  (b) quality gate passed (or not applicable)

Output is bounded, transparent, and monotonically non-decreasing per task.
"""

import logging
from typing import List

from autonomy.models import CompanyStateSnapshot, MilestoneProgress, MilestoneStatus

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Computes overall progress from a CompanyStateSnapshot.
    Stateless — safe to reuse across objectives.
    """

    def compute(self, snapshot: CompanyStateSnapshot) -> float:
        """
        Returns objective progress as 0.0 – 1.0.
        Uses snapshot.overall_progress (already computed by StateObserver)
        but applies additional validation and bounding.
        """
        progress = snapshot.overall_progress

        # Hard bounds
        progress = max(0.0, min(1.0, progress))

        # Do NOT count blocked tasks as progress
        if snapshot.blocked_task_count > 0 and progress > 0.95:
            # Never show 100% if there are blocked tasks
            progress = min(progress, 0.95)

        return round(progress, 2)

    def compute_milestone_completion(
        self, milestone_progress: List[MilestoneProgress]
    ) -> float:
        """
        Returns fraction of milestones fully completed.
        Useful for completion validation.
        """
        if not milestone_progress:
            return 0.0
        completed = sum(
            1 for m in milestone_progress
            if m.status == MilestoneStatus.COMPLETED
        )
        return round(completed / len(milestone_progress), 2)

    def is_making_progress(
        self,
        current_progress: float,
        previous_progress: float,
        tolerance: float = 0.01,
    ) -> bool:
        """
        Returns True if meaningful progress has been made since last check.
        Used by loop detection to identify stalled objectives.
        """
        return (current_progress - previous_progress) >= tolerance
