"""
Failure Analyzer (Phase 16)

Classifies failures and determines recoverability to guide the decision engine.

Failure types and their default recovery strategies:
  TRANSIENT   → RETRY (bounded, exponential backoff recommended)
  RESOURCE    → RETRY with different candidate, or REPLAN
  CAPABILITY  → REPLAN (request upskill or alternative team)
  QUALITY     → RETRY / REPLAN (revision, not just re-run)
  DEPENDENCY  → wait or REPLAN (unblock dependency chain)
  POLICY      → ESCALATE (autonomy cannot resolve policy conflicts)
  TIMEOUT     → REPLAN (reprioritize or drop scope)
  SYSTEM      → ESCALATE (unexpected; human intervention needed)

Loop detection is consulted — if max retries exceeded, override to ESCALATE.
"""

import logging
from typing import Dict, Optional

from autonomy.models import (
    FailureType, FailureAnalysisResult
)

logger = logging.getLogger(__name__)

_DEFAULT_RECOMMENDATIONS = {
    FailureType.TRANSIENT:   "RETRY",
    FailureType.RESOURCE:    "RETRY",
    FailureType.CAPABILITY:  "REPLAN",
    FailureType.QUALITY:     "REPLAN",
    FailureType.DEPENDENCY:  "REPLAN",
    FailureType.POLICY:      "ESCALATE",
    FailureType.TIMEOUT:     "REPLAN",
    FailureType.SYSTEM:      "ESCALATE",
}

_NON_RECOVERABLE = {FailureType.POLICY, FailureType.SYSTEM}


class ObjectiveFailureAnalyzer:
    """
    Classifies a failure and determines the appropriate recovery action.
    Stateless — safe to reuse across objectives.
    """

    def analyze(
        self,
        failure_description: str,
        failure_type: Optional[FailureType] = None,
        retry_count: int = 0,
        max_retries: int = 3,
        replan_count: int = 0,
        max_replans: int = 5,
        loop_detected: bool = False,
    ) -> FailureAnalysisResult:
        """
        Parameters
        ----------
        failure_description  Human-readable failure message.
        failure_type         Classified failure type, or None for auto-classify.
        retry_count          How many times this task has already been retried.
        max_retries          Max retries allowed for this task.
        replan_count         How many times the plan has been revised.
        max_replans          Max replans allowed.
        loop_detected        If True, override recommendation to ESCALATE.
        """
        # Auto-classify if not provided
        ft = failure_type or self._classify(failure_description)

        # Determine recoverability
        recoverable = ft not in _NON_RECOVERABLE

        # Determine recommendation
        recommendation = _DEFAULT_RECOMMENDATIONS.get(ft, "ESCALATE")

        # Override if limits are exhausted
        if loop_detected:
            recommendation = "ESCALATE"
            recoverable = False
            reason = f"Loop detected — escalating instead of {recommendation}."
        elif recommendation == "RETRY" and retry_count >= max_retries:
            recommendation = "REPLAN"
            reason = f"Max retries ({max_retries}) reached for {ft.value} failure."
        elif recommendation == "REPLAN" and replan_count >= max_replans:
            recommendation = "ESCALATE"
            recoverable = False
            reason = f"Max replans ({max_replans}) reached — escalating."
        else:
            reason = failure_description

        return FailureAnalysisResult(
            failure_type=ft,
            recoverable=recoverable,
            recommendation=recommendation,
            reason=reason,
            loop_detected=loop_detected,
        )

    def _classify(self, description: str) -> FailureType:
        """Keyword-based classification — no LLM."""
        desc = description.lower()
        if any(k in desc for k in ["timeout", "deadline", "expired"]):
            return FailureType.TIMEOUT
        if any(k in desc for k in ["policy", "permission", "unauthorized", "denied"]):
            return FailureType.POLICY
        if any(k in desc for k in ["quality", "gate", "validation failed"]):
            return FailureType.QUALITY
        if any(k in desc for k in ["capability", "skill", "no employee", "no candidate"]):
            return FailureType.CAPABILITY
        if any(k in desc for k in ["unavailable", "busy", "resource", "workload"]):
            return FailureType.RESOURCE
        if any(k in desc for k in ["dependency", "depends on", "blocked by"]):
            return FailureType.DEPENDENCY
        if any(k in desc for k in ["transient", "retry", "temporary", "api error", "rate limit"]):
            return FailureType.TRANSIENT
        return FailureType.SYSTEM   # Unknown — treat as system failure
