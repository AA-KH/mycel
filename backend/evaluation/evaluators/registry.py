"""
Evaluator Registry (Phase 13)

Resolves Evaluators based on EvaluationMethod.
"""

from typing import Dict, Type
from evaluation.models import EvaluationMethod
from evaluation.evaluators.base import Evaluator


class EvaluationRegistry:
    def __init__(self):
        self._evaluators: Dict[EvaluationMethod, Evaluator] = {}

    def register(self, evaluator: Evaluator):
        self._evaluators[evaluator.method] = evaluator

    def get_evaluator(self, method: EvaluationMethod) -> Evaluator:
        if method not in self._evaluators:
            raise ValueError(f"No evaluator registered for method: {method}")
        return self._evaluators[method]
