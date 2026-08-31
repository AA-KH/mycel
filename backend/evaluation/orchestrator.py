"""
Evaluation Orchestrator (Phase 13)

Service facade integrating the repository, registry, policy, and aggregator.
Runs synchronously by default, but built to support async wrapping later.
"""

import uuid
from typing import Optional, List, Tuple
from evaluation.models import Evaluation, EvaluationStatus, EvaluationType, EvaluationDimension
from evaluation.policy import EvaluationPolicy
from evaluation.evaluators.registry import EvaluationRegistry
from evaluation.evaluators.base import EvaluationContext
from evaluation.aggregator import EvaluationAggregator
from evaluation.repository import EvaluationRepository


class EvaluationOrchestrator:
    def __init__(self, registry: EvaluationRegistry, repository: EvaluationRepository, aggregator: EvaluationAggregator):
        self.registry = registry
        self.repository = repository
        self.aggregator = aggregator

    async def evaluate_target(self, 
                              policy: EvaluationPolicy, 
                              context: EvaluationContext, 
                              evaluation_id: Optional[str] = None) -> Tuple[Evaluation, Optional[str]]:
        """
        Orchestrates the evaluation process for a given policy and context.
        """
        if not evaluation_id:
            evaluation_id = f"eval_{uuid.uuid4().hex[:12]}"
            
        evaluation = Evaluation(
            evaluation_id=evaluation_id,
            evaluation_type=policy.target_type,
            status=EvaluationStatus.RUNNING,
            task_id=context.task.task_id if context.task else None,
            work_unit_id=context.work_unit.work_unit_id if context.work_unit else None,
            policy_version=policy.version
        )
        
        evaluated_dimensions: List[EvaluationDimension] = []
        
        # 1. Run all evaluators for each dimension in the policy
        for dim_config in policy.dimensions:
            try:
                # Security: Semantic evaluation is only permitted if the policy allows it
                if dim_config.method.value == "LLM_ASSISTED" and not policy.allows_semantic:
                    # Skip LLM if not explicitly allowed, but record it as not evaluated
                    evaluated_dimensions.append(
                        EvaluationDimension(
                            name=dim_config.name,
                            score=None,
                            max_score=dim_config.max_score,
                            weight=dim_config.weight,
                            method=dim_config.method,
                            evaluated=False
                        )
                    )
                    continue
                    
                evaluator = self.registry.get_evaluator(dim_config.method)
                dimension_result = await evaluator.evaluate(dim_config, context)
                evaluated_dimensions.append(dimension_result)
                
            except Exception as e:
                # We record the dimension as missing/not evaluated
                evaluated_dimensions.append(
                    EvaluationDimension(
                        name=dim_config.name,
                        score=None,
                        max_score=dim_config.max_score,
                        weight=dim_config.weight,
                        method=dim_config.method,
                        evaluated=False
                    )
                )

        # 2. Aggregate Scores
        final_score, has_partial_failures = self.aggregator.aggregate(evaluated_dimensions)
        
        # 3. Finalize Evaluation Model
        evaluation.dimensions = evaluated_dimensions
        evaluation.score = final_score
        
        if has_partial_failures:
            evaluation.status = EvaluationStatus.PARTIAL
        else:
            evaluation.status = EvaluationStatus.COMPLETED
            
        # Collect evidence across dimensions
        for dim in evaluated_dimensions:
            evaluation.evidence.extend(dim.evidence)

        # 4. Save to Repository
        saved, err = await self.repository.update(evaluation)
        return saved, err
