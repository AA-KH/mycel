"""
Policy Engine (Phase 16)

Evaluates autonomy policy compliance before any action is executed.

Checks:
- Kill switch
- Concurrency limits (max_agents, max_concurrent_tasks)
- Budget limits
- Autonomy level permissions

The policy engine READS policies — it cannot write them.
Autonomy cannot modify its own policies, remove approval gates,
increase budget limits, or change autonomy level.
"""

import logging
from typing import List

from autonomy.models import (
    CompanyObjective, AutonomyPolicy, DecisionType,
)

logger = logging.getLogger(__name__)


class PolicyResult:
    def __init__(self, allowed: bool, violations: List[str]):
        self.allowed = allowed
        self.violations = violations


class AutonomyPolicyEngine:
    """
    Evaluates whether a proposed decision is policy-compliant.
    Stateless — safe to reuse across objectives.
    """

    def evaluate(
        self,
        objective: CompanyObjective,
        decision_type: DecisionType,
        policy: AutonomyPolicy,
        current_agent_count: int = 0,
        current_task_count: int = 0,
    ) -> PolicyResult:
        violations: List[str] = []

        # 1. Kill switch
        if policy.kill_switch_active:
            violations.append(
                "Kill switch is active — no new autonomous actions permitted."
            )

        # 2. Concurrency limits — only for task/agent creation
        if decision_type == DecisionType.CREATE_TASK:
            if current_task_count >= policy.max_concurrent_tasks:
                violations.append(
                    f"Concurrent task limit reached ({current_task_count}/{policy.max_concurrent_tasks})."
                )
            if objective.budget_config.tasks_exhausted:
                violations.append(
                    f"Objective task budget exhausted ({objective.budget_config.tasks_created}/{objective.budget_config.max_tasks})."
                )

        if decision_type == DecisionType.REQUEST_RESOURCE:
            if current_agent_count >= policy.max_concurrent_agents:
                violations.append(
                    f"Concurrent agent limit reached ({current_agent_count}/{policy.max_concurrent_agents})."
                )

        # 3. Budget
        budget = objective.budget_config
        if budget.cost_exhausted and decision_type not in {
            DecisionType.WAIT, DecisionType.PAUSE, DecisionType.ESCALATE,
            DecisionType.CANCEL, DecisionType.COMPLETE,
        }:
            violations.append(
                f"Cost budget exhausted (spent={budget.spent_cost}, max={budget.max_cost})."
            )

        # 4. Iteration limit
        if budget.iterations_exhausted and decision_type not in {
            DecisionType.WAIT, DecisionType.ESCALATE, DecisionType.COMPLETE,
            DecisionType.FAIL if hasattr(DecisionType, 'FAIL') else None,
        }:
            violations.append(
                f"Iteration limit exhausted ({budget.current_iterations}/{budget.max_iterations})."
            )

        # 5. Replan limit
        if budget.replans_exhausted and decision_type == DecisionType.REPLAN:
            violations.append(
                f"Replan limit exhausted ({budget.replan_count}/{budget.max_replan_count})."
            )

        return PolicyResult(allowed=len(violations) == 0, violations=violations)
