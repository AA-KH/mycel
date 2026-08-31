from abc import ABC, abstractmethod
from typing import Dict, Any
from .result import ToolRequest, ToolResult, VerificationResult

class ToolGateway(ABC):
    @abstractmethod
    async def execute(self, request: ToolRequest) -> ToolResult:
        pass

class ResultVerifier(ABC):
    @abstractmethod
    async def verify(self, task: Dict[str, Any], result: Any, expected_output: Dict[str, Any]) -> VerificationResult:
        pass

class MemoryProvider(ABC):
    @abstractmethod
    async def get_context(self, employee_id: str, task_id: str, query: str) -> str:
        pass
        
    @abstractmethod
    async def store_memory(self, employee_id: str, task_id: str, content: str) -> None:
        pass

class ArtifactManager(ABC):
    @abstractmethod
    async def register_artifact(self, execution_id: str, content: Any, artifact_type: str) -> str:
        pass
