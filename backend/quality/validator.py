from core.errors import DomainError
from .models import QualityGate

class QualityGateValidator:
    """
    Validates the structural integrity of a QualityGate definition.
    """
    
    @staticmethod
    def validate_gate(gate: QualityGate):
        if not gate.quality_gate_id:
            raise DomainError("quality_gate_id is required.")
            
        if not gate.name:
            raise DomainError("QualityGate must have a name.")
            
        # Check uniqueness of check_ids within this gate
        check_ids = set()
        for check in gate.checks:
            if check.check_id in check_ids:
                raise DomainError(f"Duplicate check_id '{check.check_id}' found in QualityGate '{gate.quality_gate_id}'")
            check_ids.add(check.check_id)
