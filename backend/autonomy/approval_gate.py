"""
Approval Gate (Phase 16)

Evaluates whether an action requires human approval before execution.

Action categories and their default approval requirements:
  READ_ONLY             → never requires approval
  REVERSIBLE            → depends on risk level vs. policy threshold
  IRREVERSIBLE          → approval required by default (policy can lower threshold)
  EXTERNAL_SIDE_EFFECT  → approval required by default

Risk levels map to ordinal values:
  LOW=0, MEDIUM=1, HIGH=2, CRITICAL=3

Autonomy Level overrides:
  MANUAL     → ALL actions require approval
  ASSISTED   → ALL actions require approval
  SUPERVISED → actions at or above policy.require_approval_threshold
  AUTONOMOUS → only IRREVERSIBLE / EXTERNAL_SIDE_EFFECT / CRITICAL require approval

The gate does NOT:
- Execute the action
- Modify policies
- Bypass any rules
- Grant itself permissions
"""

import logging

from autonomy.models import (
    ActionCategory, RiskLevel, AutonomyLevel, AutonomyPolicy,
    ApprovalResult, DecisionType,
)

logger = logging.getLogger(__name__)

_RISK_ORDER = {
    RiskLevel.LOW:      0,
    RiskLevel.MEDIUM:   1,
    RiskLevel.HIGH:     2,
    RiskLevel.CRITICAL: 3,
}

# Decisions that are always READ_ONLY regardless of other factors
_ALWAYS_READ_ONLY = {DecisionType.WAIT, DecisionType.PAUSE}

# Decisions that are always considered high-risk
_ALWAYS_HIGH_RISK = {DecisionType.CANCEL}

# Decisions that are IRREVERSIBLE by nature
_ALWAYS_IRREVERSIBLE = set()   # Populated per-deployment policy


class ApprovalGate:
    """
    Evaluates whether an action requires human approval.
    Stateless — safe to use concurrently.
    """

    def check(
        self,
        decision_type: DecisionType,
        action_category: ActionCategory,
        risk_level: RiskLevel,
        autonomy_level: AutonomyLevel,
        policy: AutonomyPolicy,
    ) -> ApprovalResult:
        """
        Returns ApprovalResult indicating whether approval is required.
        """
        # Kill switch — handled upstream, not here

        # 1. MANUAL and ASSISTED — all non-trivial actions require approval
        if autonomy_level in (AutonomyLevel.MANUAL, AutonomyLevel.ASSISTED):
            if decision_type not in _ALWAYS_READ_ONLY:
                return ApprovalResult(
                    required=True,
                    reason=f"Autonomy level is {autonomy_level.value} — human approval required for all actions.",
                    gate_name="autonomy_level_gate",
                    risk_level=risk_level,
                )

        # 2. READ_ONLY actions never require approval
        if action_category == ActionCategory.READ_ONLY or decision_type in _ALWAYS_READ_ONLY:
            return ApprovalResult(
                required=False,
                reason="READ_ONLY action — no approval required.",
                gate_name="read_only_gate",
                risk_level=risk_level,
            )

        # 3. IRREVERSIBLE / EXTERNAL_SIDE_EFFECT — approval required by default
        if action_category in (ActionCategory.IRREVERSIBLE, ActionCategory.EXTERNAL_SIDE_EFFECT):
            if not policy.allow_irreversible_actions:
                return ApprovalResult(
                    required=True,
                    reason=(
                        f"Action category is {action_category.value}. "
                        f"Policy requires approval for irreversible/external actions."
                    ),
                    gate_name="irreversible_gate",
                    risk_level=risk_level,
                )

        # 4. AUTONOMOUS level — only critical actions require approval at this point
        if autonomy_level == AutonomyLevel.AUTONOMOUS:
            if risk_level == RiskLevel.CRITICAL:
                return ApprovalResult(
                    required=True,
                    reason="CRITICAL risk action requires approval even in AUTONOMOUS mode.",
                    gate_name="critical_gate",
                    risk_level=risk_level,
                )
            return ApprovalResult(
                required=False,
                reason="Action is within autonomous execution boundaries.",
                gate_name="autonomous_gate",
                risk_level=risk_level,
            )

        # 5. Risk level threshold
        policy_threshold = _RISK_ORDER.get(policy.require_approval_threshold, 2)
        action_risk = _RISK_ORDER.get(risk_level, 0)

        if action_risk >= policy_threshold:
            return ApprovalResult(
                required=True,
                reason=(
                    f"Action risk level {risk_level.value} meets or exceeds "
                    f"policy approval threshold {policy.require_approval_threshold.value}."
                ),
                gate_name="risk_threshold_gate",
                risk_level=risk_level,
            )

        return ApprovalResult(
            required=False,
            reason="Action is within supervised execution boundaries.",
            gate_name="default_gate",
            risk_level=risk_level,
        )
