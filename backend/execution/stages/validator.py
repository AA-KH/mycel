from core.errors import DomainError
from .models import StageDefinition

class StageDefinitionValidator:
    """
    Validates the intrinsic structure of a StageDefinition.
    Does not validate external dependencies (e.g., verifying if the Skill exists in DB).
    """
    
    @staticmethod
    def validate_definition(definition: StageDefinition):
        if not definition.stage_definition_id:
            raise DomainError("stage_definition_id is required.")
            
        if not definition.purpose:
            raise DomainError("StageDefinition must have a clear 'purpose'.")
            
        if not definition.input_contract.input_type:
            raise DomainError("StageInputContract requires an 'input_type'.")
            
        if not definition.requirement_contract.output_contract_id:
            raise DomainError("Stage requires an output_contract_id.")
            
        # Validate failure policy
        if definition.failure_policy.max_attempts > 5:
            raise DomainError("StageFailurePolicy max_attempts cannot exceed 5.")
