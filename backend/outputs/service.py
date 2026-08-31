from typing import Any, Dict
from .models import OutputContract, ArtifactPolicy, OutputPackageContract, OutputType
from .results import OutputValidationResult, OutputViolation, OutputViolationSeverity

class OutputContractValidationService:
    
    @staticmethod
    def validate(contract: OutputContract, actual_output: Dict[str, Any]) -> OutputValidationResult:
        violations = []
        
        # 1. Package handling
        if contract.output_type == OutputType.PACKAGE and isinstance(contract, OutputPackageContract):
            # For a package, actual_output should map output_contract_id -> inner actual output
            for inner_contract in contract.outputs:
                inner_actual = actual_output.get(inner_contract.output_contract_id)
                
                if not inner_actual:
                    violations.append(OutputViolation(
                        field=inner_contract.output_contract_id,
                        expected="Present",
                        actual="Missing",
                        code="MISSING_PACKAGE_OUTPUT",
                        message=f"Missing required inner output '{inner_contract.output_contract_id}'"
                    ))
                else:
                    # Recursively validate inner contract
                    inner_res = OutputContractValidationService.validate(inner_contract, inner_actual)
                    violations.extend(inner_res.violations)
            
            return OutputValidationResult(
                valid=len(violations) == 0,
                contract_id=contract.output_contract_id,
                contract_version=contract.version,
                actual_output=actual_output,
                violations=violations
            )
            
        # 2. Artifact Policy
        artifact_ref = actual_output.get("artifact_reference")
        if contract.artifact_policy == ArtifactPolicy.REQUIRED and not artifact_ref:
            violations.append(OutputViolation(
                field="artifact_reference",
                expected="Present",
                actual="Missing",
                code="MISSING_REQUIRED_ARTIFACT",
                message="Contract requires a physical ArtifactReference but none was provided."
            ))
            
        # 3. Format validation
        if artifact_ref and contract.formats:
            actual_format = artifact_ref.get("format")
            if actual_format not in contract.formats:
                violations.append(OutputViolation(
                    field="format",
                    expected=contract.formats,
                    actual=actual_format,
                    code="INVALID_FORMAT",
                    message=f"Artifact format '{actual_format}' is not in allowed formats {contract.formats}."
                ))
                
        # 4. Metadata Requirements Validation
        actual_metadata = actual_output.get("metadata", {})
        if artifact_ref and "metadata" in artifact_ref:
             # Merge artifact metadata for validation
             actual_metadata.update(artifact_ref.get("metadata", {}))
             
        for k, v in contract.metadata_requirements.items():
            actual_val = actual_metadata.get(k)
            if actual_val != v:
                violations.append(OutputViolation(
                    field=f"metadata.{k}",
                    expected=v,
                    actual=actual_val,
                    code="METADATA_MISMATCH",
                    message=f"Expected metadata {k}={v}, got {actual_val}."
                ))

        # We do not validate content_requirements here; they are declarative for Quality Gates.
        
        return OutputValidationResult(
            valid=len(violations) == 0,
            contract_id=contract.output_contract_id,
            contract_version=contract.version,
            actual_output=actual_output,
            violations=violations
        )
