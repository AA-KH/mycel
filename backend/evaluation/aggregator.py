"""
Evaluation Aggregator (Phase 13)

Responsible for combining dimension scores using policy weights, handling missing 
dimensions, and producing the final evaluation score.
"""

from typing import List, Tuple
from evaluation.models import EvaluationDimension


class EvaluationAggregator:
    def aggregate(self, dimensions: List[EvaluationDimension]) -> Tuple[float, bool]:
        """
        Computes the weighted overall score.
        Returns (score, has_partial_failures).
        
        If a REQUIRED dimension is evaluated as 0.0 or is missing, we consider this a partial/critical failure.
        However, the score is still mathematically computed.
        """
        total_weight = 0.0
        weighted_sum = 0.0
        
        has_partial_failures = False
        
        for dim in dimensions:
            if not dim.evaluated:
                # We skip missing dimensions instead of treating them as 0, 
                # unless a specific strict policy says otherwise.
                continue
                
            if dim.score is None:
                continue
                
            total_weight += dim.weight
            
            # Normalize to 0-1 scale if max_score > 1.0 (though it's usually 1.0)
            normalized_score = dim.score / dim.max_score if dim.max_score > 0 else 0.0
            weighted_sum += (normalized_score * dim.weight)
            
            if normalized_score == 0.0:
                has_partial_failures = True
                
        if total_weight == 0.0:
            return 0.0, True  # Nothing was successfully evaluated
            
        final_score = weighted_sum / total_weight
        return final_score, has_partial_failures
