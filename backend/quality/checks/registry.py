from typing import Dict, Type
from ..models import QualityCheckType
from .base import BaseQualityCheckExecutor

class QualityCheckRegistry:
    def __init__(self):
        self._executors: Dict[QualityCheckType, BaseQualityCheckExecutor] = {}
        
    def register(self, executor: BaseQualityCheckExecutor):
        self._executors[executor.check_type] = executor
        
    def get_executor(self, check_type: QualityCheckType) -> BaseQualityCheckExecutor:
        executor = self._executors.get(check_type)
        if not executor:
            raise NotImplementedError(f"No executor registered for QualityCheckType: {check_type}")
        return executor
