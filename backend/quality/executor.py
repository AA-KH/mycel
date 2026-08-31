import logging
from typing import List

from .models import QualityGate, QualityPolicy, QualityGateDecision, QualityCheckSeverity
from .results import QualityGateResult, QualityCheckResult, QualityCheckResultStatus
from .checks.base import QualityEvaluationContext
from .checks.registry import QualityCheckRegistry

logger = logging.getLogger(__name__)

class QualityGateExecutor:
    """
    Evaluates a QualityGate against a given context.
    """
    def __init__(self, check_registry: QualityCheckRegistry):
        self.check_registry = check_registry

    async def evaluate(self, gate: QualityGate, context: QualityEvaluationContext) -> QualityGateResult:
        check_results: List[QualityCheckResult] = []
        failure_reasons: List[str] = []
        
        # 1. Execute all checks (sorted by order for logical flow, though conceptually independent)
        sorted_checks = sorted(gate.checks, key=lambda c: c.order)
        
        for check in sorted_checks:
            try:
                executor = self.check_registry.get_executor(check.type)
                result = await executor.execute(check, context)
            except Exception as e:
                logger.error(f"Error executing QualityCheck {check.check_id} of type {check.type}: {e}")
                result = QualityCheckResult(
                    check_id=check.check_id,
                    status=QualityCheckResultStatus.ERROR,
                    message=f"Execution error: {str(e)}"
                )
            
            check_results.append(result)
            
            # Record explicit failure reasons
            if result.status == QualityCheckResultStatus.FAIL:
                failure_reasons.append(f"Check '{check.name}' failed: {result.message}")
            elif result.status == QualityCheckResultStatus.ERROR:
                failure_reasons.append(f"Check '{check.name}' encountered error: {result.message}")
        
        # 2. Apply Policy to determine final decision
        decision = self._apply_policy(gate, check_results, failure_reasons)
        
        # 3. Compile Result
        gate_result = QualityGateResult(
            quality_gate_id=gate.quality_gate_id,
            version=gate.version,
            execution_id=context.execution_id,
            stage_execution_id=context.stage_execution_id,
            pipeline_execution_id=context.pipeline_execution_id,
            decision=decision,
            check_results=check_results,
            failure_reasons=failure_reasons
        )
        
        return gate_result

    def _apply_policy(
        self, gate: QualityGate, results: List[QualityCheckResult], failure_reasons: List[str]
    ) -> QualityGateDecision:
        
        # Helper maps
        result_map = {r.check_id: r for r in results}
        
        has_critical_failure = False
        has_required_failure = False
        
        for check in gate.checks:
            res = result_map.get(check.check_id)
            if not res:
                if check.required:
                    has_required_failure = True
                    failure_reasons.append(f"Check '{check.name}' missing result.")
                continue
                
            is_failure = res.status in (QualityCheckResultStatus.FAIL, QualityCheckResultStatus.ERROR)
            
            if is_failure:
                if check.required:
                    has_required_failure = True
                if check.severity == QualityCheckSeverity.CRITICAL:
                    has_critical_failure = True

        # Policy: ALL_REQUIRED_PASS
        if gate.policy == QualityPolicy.ALL_REQUIRED_PASS:
            if has_required_failure:
                # Decide if we retry or fail based on severity, but standard mapping:
                if has_critical_failure:
                    return QualityGateDecision.FAIL
                return QualityGateDecision.RETRY
            return QualityGateDecision.PASS
            
        # Policy: CRITICAL_FAILURE_BLOCKS
        elif gate.policy == QualityPolicy.CRITICAL_FAILURE_BLOCKS:
            if has_critical_failure:
                return QualityGateDecision.BLOCK
            if has_required_failure:
                return QualityGateDecision.RETRY
            return QualityGateDecision.PASS
            
        # Fallback Default
        if has_required_failure:
            return QualityGateDecision.FAIL
            
        return QualityGateDecision.PASS
