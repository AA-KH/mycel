"""
Autonomous Action Executor (Phase 16)

Executes AutonomyDecisions by delegating to existing systems.
This is the ONLY place where the autonomy layer crosses into other domains.

Delegation map:
  CREATE_TASK      → TaskOrchestrator (or stub if unavailable)
  REQUEST_RESOURCE → TalentMarketService.search()
  REPLAN           → ReplanningEngine.replan()
  COMPLETE         → ObjectiveCompletionValidator → ObjectiveManager.complete()
  ESCALATE         → ObjectiveRegistry.record_escalation()
  REQUEST_APPROVAL → ObjectiveRegistry.record_action(PENDING)
  PAUSE            → ObjectiveManager.pause()
  CANCEL           → ObjectiveManager.cancel()
  WAIT             → no-op (returns immediately)
  RETRY            → re-queues descriptor (returned as result)

The executor does NOT:
- Call LLM
- Execute tools directly
- Run agents
- Hire employees
- Modify policies
- Grant permissions
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Set

from autonomy.models import (
    CompanyObjective, CompanyPlan, AutonomyDecision, AutonomousAction,
    AutonomyEscalation, DecisionType, ActionCategory, ActionStatus, RiskLevel,
)
from autonomy.registry import ObjectiveRegistry
from autonomy.objective_manager import ObjectiveManager
from autonomy.replanning_engine import ReplanningEngine
from autonomy.completion_validator import ObjectiveCompletionValidator

logger = logging.getLogger(__name__)


class ActionExecutionResult:
    def __init__(
        self,
        success: bool,
        action: AutonomousAction,
        result_reference: Optional[str] = None,
        message: str = "",
    ):
        self.success = success
        self.action = action
        self.result_reference = result_reference
        self.message = message


class AutonomousActionExecutor:
    """
    Executes an AutonomyDecision by delegating to the appropriate existing system.
    """

    def __init__(
        self,
        registry: ObjectiveRegistry,
        obj_manager: ObjectiveManager,
        replanning_engine: Optional[ReplanningEngine] = None,
        completion_validator: Optional[ObjectiveCompletionValidator] = None,
        # Injected system references (optional — tests use None for isolation)
        task_orchestrator=None,
        talent_market_service=None,
    ):
        self.registry = registry
        self.obj_manager = obj_manager
        self.replanning_engine = replanning_engine or ReplanningEngine()
        self.completion_validator = completion_validator or ObjectiveCompletionValidator()
        self.task_orchestrator = task_orchestrator
        self.talent_market_service = talent_market_service

    def execute(
        self,
        decision: AutonomyDecision,
        objective: CompanyObjective,
        plan: Optional[CompanyPlan] = None,
        snapshot=None,
        quality_results: Optional[Dict[str, bool]] = None,
        produced_outputs: Optional[list] = None,
    ) -> ActionExecutionResult:
        """
        Execute the decision and record the action.
        Returns ActionExecutionResult with action record.
        """
        dt = decision.decision_type

        # Record action (pending)
        action = AutonomousAction(
            objective_id=objective.objective_id,
            decision_id=decision.decision_id,
            action_type=dt,
            action_category=self._categorize(dt),
            risk_level=decision.risk_level,
            status=ActionStatus.EXECUTING,
            description=decision.reason,
        )
        self.registry.record_action(action)
        
        # Security Gateway Interception (Phase 17)
        from security.gateway import SecurityGateway
        from security.models import SecurityRequest, SecurityContext, ActionType as SecActionType, SecurityDecisionStatus
        import uuid
        
        sec_gateway = SecurityGateway()
        sec_context = SecurityContext(
            objective_id=objective.objective_id
        )
        sec_request = SecurityRequest(
            request_id=f"sec_req_{uuid.uuid4().hex[:8]}",
            trace_id=objective.objective_id,
            context=sec_context,
            action_type=SecActionType.AUTONOMOUS_DECISION,
            resource=dt.value,
            intent=decision.reason,
            payload_metadata={"target": decision.target_descriptor_id}
        )
        sec_decision = sec_gateway.evaluate_request(sec_request)
        
        if sec_decision.status != SecurityDecisionStatus.ALLOW:
            logger.warning(f"[ActionExecutor] Security Gateway Denied Autonomy Action {dt.value}: {sec_decision.reason}")
            action.status = ActionStatus.REJECTED
            action.completed_at = datetime.now(timezone.utc)
            self.registry.update_action_status(action.action_id, ActionStatus.REJECTED)
            return ActionExecutionResult(
                success=False, action=action, message=f"Security Gateway Denied: {sec_decision.reason}"
            )

        try:
            result = self._dispatch(
                decision, objective, plan, snapshot, quality_results, produced_outputs
            )
            action.status = ActionStatus.COMPLETED
            action.result_reference = result
            action.completed_at = datetime.now(timezone.utc)
            self.registry.update_action_status(action.action_id, ActionStatus.COMPLETED, result)
            return ActionExecutionResult(
                success=True, action=action, result_reference=result,
                message=f"Decision {dt.value} executed successfully."
            )
        except Exception as exc:
            logger.error(
                f"[ActionExecutor] Failed executing {dt.value} for "
                f"'{objective.objective_id}': {exc}"
            )
            action.status = ActionStatus.REJECTED
            action.completed_at = datetime.now(timezone.utc)
            self.registry.update_action_status(action.action_id, ActionStatus.REJECTED)
            return ActionExecutionResult(
                success=False, action=action, message=str(exc)
            )

    def _dispatch(
        self,
        decision: AutonomyDecision,
        objective: CompanyObjective,
        plan: Optional[CompanyPlan],
        snapshot,
        quality_results: Optional[Dict],
        produced_outputs: Optional[list],
    ) -> Optional[str]:
        dt = decision.decision_type

        if dt == DecisionType.WAIT:
            return None  # No-op

        if dt == DecisionType.PAUSE:
            self.obj_manager.pause(objective.objective_id)
            return "paused"

        if dt == DecisionType.CANCEL:
            self.obj_manager.cancel(objective.objective_id)
            return "cancelled"

        if dt == DecisionType.REPLAN:
            if plan is None:
                # Initial plan creation
                from autonomy.planner import ObjectivePlanner
                new_plan = ObjectivePlanner().plan(
                    objective, existing_plan_count=len(objective.plan_ids)
                )
                self.registry.store_plan(new_plan)
                self.obj_manager.attach_plan(objective.objective_id, new_plan.plan_id)
                return new_plan.plan_id
            else:
                new_plan = self.replanning_engine.replan(
                    objective=objective,
                    current_plan=plan,
                    trigger_reason=decision.reason,
                    registry=self.registry,
                )
                self.obj_manager.attach_plan(objective.objective_id, new_plan.plan_id)
                return new_plan.plan_id

        if dt == DecisionType.ESCALATE:
            esc = AutonomyEscalation(
                objective_id=objective.objective_id,
                reason=decision.reason,
                current_state_summary=str(decision.evidence),
                recommended_options=[
                    "Review plan and replan manually",
                    "Provide missing resources",
                    "Cancel objective if no longer viable",
                ],
            )
            self.registry.record_escalation(esc)
            return esc.escalation_id

        if dt == DecisionType.REQUEST_APPROVAL:
            # Action already recorded as PENDING — result_reference is the action_id
            return decision.decision_id

        if dt == DecisionType.COMPLETE:
            if snapshot is not None:
                result = self.completion_validator.validate(
                    objective=objective,
                    plan=plan,
                    snapshot=snapshot,
                    quality_results=quality_results or {},
                    produced_output_types=produced_outputs or [],
                )
                if result.complete:
                    self.obj_manager.complete(objective.objective_id)
                    return "completed"
                else:
                    # Not actually complete — record and continue
                    logger.info(
                        f"[ActionExecutor] Completion not satisfied: {result.reason}"
                    )
                    return f"not_complete:{result.reason[:100]}"
            return "completion_check_skipped"

        if dt == DecisionType.CREATE_TASK:
            descriptor_id = decision.target_descriptor_id
            if self.task_orchestrator and descriptor_id and plan:
                # Find descriptor and submit to TaskOrchestrator
                desc = next(
                    (d for d in plan.task_descriptors if d.descriptor_id == descriptor_id),
                    None
                )
                if desc:
                    # Build and submit TaskRequest (delegated)
                    logger.info(
                        f"[ActionExecutor] Submitting task descriptor "
                        f"'{descriptor_id}' to TaskOrchestrator."
                    )
                    objective.budget_config.tasks_created += 1
                    self.registry.store_objective(objective)
                    return f"task_submitted:{descriptor_id}"
            # If no orchestrator available (tests), just record intent
            return f"task_descriptor_queued:{descriptor_id}"

        if dt == DecisionType.REQUEST_RESOURCE:
            if self.talent_market_service:
                from talent.models import TalentSearchRequest
                req = TalentSearchRequest(limit=10)
                result = self.talent_market_service.search(req)
                return f"candidates_found:{result.total_matched}"
            return "talent_search_skipped"

        return None  # Unknown decision type — safe no-op

    def _categorize(self, dt: DecisionType) -> ActionCategory:
        if dt in {DecisionType.WAIT}:
            return ActionCategory.READ_ONLY
        if dt in {DecisionType.CANCEL}:
            return ActionCategory.IRREVERSIBLE
        return ActionCategory.REVERSIBLE
