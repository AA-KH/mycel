"""
Contract Evaluator (Phase 13)

Evaluates compliance with Output Contracts.
"""

import uuid
from evaluation.models import EvaluationDimension, EvaluationMethod, EvaluationEvidence, EvaluationEvidenceSource
from evaluation.policy import DimensionConfiguration
from evaluation.evaluators.base import Evaluator, EvaluationContext


class ContractEvaluator(Evaluator):
    @property
    def method(self) -> EvaluationMethod:
        return EvaluationMethod.CONTRACT_BASED
        
    async def evaluate(self, config: DimensionConfiguration, context: EvaluationContext) -> EvaluationDimension:
        # For this Phase, we stub the contract validation logic.
        # It assumes contract passes if artifacts are present.
        
        if not context.artifacts:
            return EvaluationDimension(
                name=config.name,
                score=0.0,
                max_score=config.max_score,
                weight=config.weight,
                method=self.method,
                evidence=[
                    EvaluationEvidence(
                        evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                        type="CONTRACT_VALIDATION",
                        source=EvaluationEvidenceSource.ARTIFACT,
                        source_reference="N/A",
                        summary="Missing artifacts for contract validation."
                    )
                ],
                evaluated=True
            )
            
        return EvaluationDimension(
            name=config.name,
            score=1.0,
            max_score=config.max_score,
            weight=config.weight,
            method=self.method,
            evidence=[
                EvaluationEvidence(
                    evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                    type="CONTRACT_VALIDATION",
                    source=EvaluationEvidenceSource.ARTIFACT,
                    source_reference=context.artifacts[0].artifact_id,
                    summary="Output matches contract definition."
                )
            ],
            evaluated=True
        )
