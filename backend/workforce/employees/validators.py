from typing import List, Dict, Any
from core.errors import ValidationError
from tools.registry import registry as tool_registry
from execution.reasoning.strategies import get_strategy
from .models import Employee

# Define valid artifact output types based on Phase 7 Artifact System
VALID_OUTPUT_TYPES = {
    "video", "image", "audio", "document", "pdf", 
    "presentation", "text", "raw", "source_code", "api", "test_suite",
    "research_report", "competitive_analysis", "market_report", "thumbnail"
}

class EmployeeDefinitionValidator:
    """
    Validates a Specialized Employee Definition (Phase 8).
    Ensures that the employee definition relies on valid cross-system references.
    """
    
    @classmethod
    def validate(cls, employee: Employee) -> None:
        """
        Validates an Employee object. Raises ValidationError if invalid.
        """
        cls._validate_identity(employee)
        cls._validate_skills(employee.skills)
        cls._validate_tools(employee.tools)
        cls._validate_outputs(employee.outputs)
        cls._validate_reasoning_profile(employee.reasoning_profile_id)
        
    @classmethod
    def _validate_identity(cls, employee: Employee) -> None:
        if not employee.employee_id:
            raise ValidationError("Employee ID cannot be empty.")
        if not employee.name:
            raise ValidationError("Employee name cannot be empty.")
        if not employee.team_id:
            raise ValidationError("Employee team_id cannot be empty.")
        if not employee.position_id:
            raise ValidationError("Employee position_id cannot be empty.")
            
    @classmethod
    def _validate_skills(cls, skills: Dict[str, Any]) -> None:
        for skill_id, skill in skills.items():
            if not (0 <= skill.level <= 100):
                raise ValidationError(f"Skill '{skill_id}' proficiency must be between 0 and 100.")
                
    @classmethod
    def _validate_tools(cls, tool_ids: List[str]) -> None:
        for tid in tool_ids:
            try:
                tool_registry.get_definition(tid)
            except Exception as e:
                # Catch ToolNotFoundError
                raise ValidationError(f"Invalid tool reference: '{tid}'. Tool does not exist in registry.")
                
    @classmethod
    def _validate_outputs(cls, outputs: List[str]) -> None:
        for output in outputs:
            if output not in VALID_OUTPUT_TYPES:
                raise ValidationError(f"Invalid output type: '{output}'. Must be one of {VALID_OUTPUT_TYPES}.")
                
    @classmethod
    def _validate_reasoning_profile(cls, reasoning_profile_id: str) -> None:
        if not reasoning_profile_id:
            raise ValidationError("reasoning_profile_id cannot be empty.")
            
        from execution.reasoning.strategies import VALID_STRATEGIES
        if reasoning_profile_id not in VALID_STRATEGIES:
            raise ValidationError(f"Invalid reasoning profile: '{reasoning_profile_id}'.")
