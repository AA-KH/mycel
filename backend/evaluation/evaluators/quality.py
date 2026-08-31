"""
Quality Evaluator (Phase 13)

Integrates existing Quality Gate results without re-running the gate.
"""

import uuid
from evaluation.models import EvaluationDimension, EvaluationMethod, EvaluationEvidence, EvaluationEvidenceSource
from evaluation.policy import DimensionConfiguration
from evaluation.evaluators.base import Evaluator, EvaluationContext
from quality.results import QualityGateDecision


class QualityEvaluator(Evaluator):
    @property
    def method(self) -> EvaluationMethod:
        return EvaluationMethod.QUALITY_BASED
        
    async def evaluate(self, config: DimensionConfiguration, context: EvaluationContext) -> EvaluationDimension:
        if not context.quality_results:
            return EvaluationDimension(
                name=config.name,
                score=None,
                max_score=config.max_score,
                weight=config.weight,
                method=self.method,
                evidence=[],
                evaluated=False
            )
            
        evidence_list = []
        passes = 0
        total = len(context.quality_results)
        
        for q_result in context.quality_results:
            summary = f"Gate {q_result.quality_gate_id} decision: {q_result.decision.value}"
            if q_result.failure_reasons:
                summary += f" ({len(q_result.failure_reasons)} failures)"
                
            evidence_list.append(
                EvaluationEvidence(
                    evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                    type="QUALITY_GATE_RESULT",
                    source=EvaluationEvidenceSource.QUALITY_GATE,
                    source_reference=q_result.quality_gate_id,
                    summary=summary
                )
            )
            
            if q_result.decision == QualityGateDecision.PASS:
                passes += 1
                
        # Simple proportional score based on quality gate pass rate
        score = passes / total if total > 0 else 0.0
        
        return EvaluationDimension(
            name=config.name,
            score=score,
            max_score=config.max_score,
            weight=config.weight,
            method=self.method,
            evidence=evidence_list,
            evaluated=True
        )
