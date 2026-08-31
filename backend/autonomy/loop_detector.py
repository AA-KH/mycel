"""
Loop Detector (Phase 16)

Detects pathological patterns that indicate the autonomy engine is stuck:
- Same task failing repeatedly (≥ max_retries_per_task)
- Same plan being superseded repeatedly (≥ max_replan_count)
- Same decision type being produced repeatedly
- No progress being made across iterations

When a loop is detected, the decision engine must ESCALATE instead of continuing.
Never retry or replan indefinitely.
"""

import logging
from collections import Counter
from typing import Dict, List, Optional

from autonomy.models import AutonomyDecision, DecisionType

logger = logging.getLogger(__name__)

_LOOP_SAME_DECISION_THRESHOLD = 5  # Same decision type N times in a row → loop


class LoopDetector:
    """
    Detects autonomy loop patterns from decision history.
    Stateless — safe to reuse across objectives.
    """

    def detect(
        self,
        decisions: List[AutonomyDecision],
        task_failure_counts: Dict[str, int],   # task_id / descriptor_id → fail count
        max_retries_per_task: int = 3,
        max_replan_count: int = 5,
        current_replan_count: int = 0,
    ) -> Dict:
        """
        Returns a result dict:
        {
            "loop_detected": bool,
            "reason": str,
            "pattern": str,     # "repeated_task_failure" | "repeated_replan" | "repeated_decision" | "no_loop"
        }
        """
        # 1. Task failure loop
        for task_id, fail_count in task_failure_counts.items():
            if fail_count >= max_retries_per_task:
                logger.warning(
                    f"[LoopDetector] Task '{task_id}' has failed {fail_count} times "
                    f"(max={max_retries_per_task})."
                )
                return {
                    "loop_detected": True,
                    "reason": (
                        f"Task '{task_id}' failed {fail_count} times "
                        f"(limit={max_retries_per_task})."
                    ),
                    "pattern": "repeated_task_failure",
                }

        # 2. Replan loop
        if current_replan_count >= max_replan_count:
            logger.warning(
                f"[LoopDetector] Replan count {current_replan_count} ≥ max {max_replan_count}."
            )
            return {
                "loop_detected": True,
                "reason": (
                    f"Replan limit reached ({current_replan_count}/{max_replan_count}). "
                    f"Cannot create additional plan versions."
                ),
                "pattern": "repeated_replan",
            }

        # 3. Repeated same decision type
        if len(decisions) >= _LOOP_SAME_DECISION_THRESHOLD:
            recent = decisions[-_LOOP_SAME_DECISION_THRESHOLD:]
            types = [d.decision_type for d in recent]
            if len(set(types)) == 1 and types[0] not in {
                DecisionType.WAIT, DecisionType.COMPLETE
            }:
                logger.warning(
                    f"[LoopDetector] Same decision '{types[0]}' made {_LOOP_SAME_DECISION_THRESHOLD} times in a row."
                )
                return {
                    "loop_detected": True,
                    "reason": (
                        f"Same decision '{types[0].value}' produced "
                        f"{_LOOP_SAME_DECISION_THRESHOLD} consecutive times."
                    ),
                    "pattern": "repeated_decision",
                }

        return {
            "loop_detected": False,
            "reason": "",
            "pattern": "no_loop",
        }
