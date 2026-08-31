from core.errors import DomainError
from .models import OutputContract, OutputType

class OutputContractValidator:
    """
    Validates the structural integrity of an OutputContract definition.
    """
    
    @staticmethod
    def validate_contract(contract: OutputContract):
        if not contract.output_contract_id:
            raise DomainError("output_contract_id is required.")
            
        if not contract.name:
            raise DomainError("OutputContract must have a name.")
            
        # Basic structural checks
        if contract.output_type == OutputType.VIDEO and not contract.formats:
            # We could enforce that videos must specify valid formats, but allowing empty is also fine 
            # if they accept any video format.
            pass
            
        if contract.output_type == OutputType.PACKAGE:
            from .models import OutputPackageContract
            if not isinstance(contract, OutputPackageContract):
                raise DomainError("Package outputs must use the OutputPackageContract model.")
            
            if not contract.outputs:
                raise DomainError("Package output contracts must define inner outputs.")
