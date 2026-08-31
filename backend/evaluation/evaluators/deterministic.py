"""
Deterministic Evaluator (Phase 13)

Evaluates explicit boolean metrics (e.g., existence of an artifact, file size checks).
"""

import uuid
from typing import Optional
from evaluation.models import EvaluationDimension, EvaluationMethod, EvaluationEvidence, EvaluationEvidenceSource
from evaluation.policy import DimensionConfiguration
from evaluation.evaluators.base import Evaluator, EvaluationContext


class DeterministicEvaluator(Evaluator):
    @property
    def method(self) -> EvaluationMethod:
        return EvaluationMethod.DETERMINISTIC
        
    async def evaluate(self, config: DimensionConfiguration, context: EvaluationContext) -> EvaluationDimension:
        evidence_list = []
        
        # Example logic for deterministic check.
        # In a real system, this would evaluate metadata fields from the context artifacts
        # based on config.metadata properties. For this implementation, we stub the logic.
        
        target_check = config.metadata.get("check_type")
        score = 0.0
        
        if target_check == "artifact_exists":
            if len(context.artifacts) > 0:
                score = 1.0
                evidence_list.append(
                    EvaluationEvidence(
                        evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                        type="ARTIFACT_CHECK",
                        source=EvaluationEvidenceSource.ARTIFACT,
                        source_reference=context.artifacts[0].artifact_id,
                        summary="Artifact is present."
                    )
                )
            else:
                score = 0.0
                evidence_list.append(
                    EvaluationEvidence(
                        evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
                        type="ARTIFACT_CHECK",
                        source=EvaluationEvidenceSource.ARTIFACT,
                        source_reference="N/A",
                        summary="Artifact is missing."
                    )
                )
        else:
            # If no explicit check is known, we mark it as NOT_EVALUATED
            return EvaluationDimension(
                name=config.name,
                score=None,
                max_score=config.max_score,
                weight=config.weight,
                method=self.method,
                evidence=[],
                evaluated=False
            )
        
        return EvaluationDimension(
            name=config.name,
            score=score,
            max_score=config.max_score,
            weight=config.weight,
            method=self.method,
            evidence=evidence_list,
            evaluated=True
        )
