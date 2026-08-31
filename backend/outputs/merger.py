from core.errors import DomainError
from .models import OutputContract

class OutputContractConflict(DomainError):
    def __init__(self, field: str, base_val: str, override_val: str):
        super().__init__(f"OutputContract conflict on field '{field}': '{base_val}' vs '{override_val}'")

class OutputContractMerger:
    
    @staticmethod
    def merge(base: OutputContract, override: OutputContract) -> OutputContract:
        """
        Merges two contracts. Specific overrides general only when compatible.
        Raises OutputContractConflict if incompatible.
        """
        # Ensure we are operating on identical output types, or that override is valid for base
        if base.output_type != override.output_type:
            raise OutputContractConflict("output_type", base.output_type, override.output_type)
            
        # Merge Formats
        # If base says [], override can say ["mp4"].
        # If base says ["mp4", "webm"], override can say ["mp4"].
        # If base says ["webm"], override cannot say ["mp4"].
        final_formats = base.formats
        if override.formats:
            if not base.formats:
                final_formats = override.formats
            else:
                # Override must be a subset of base formats
                invalid_formats = set(override.formats) - set(base.formats)
                if invalid_formats:
                    raise OutputContractConflict("formats", str(base.formats), str(override.formats))
                final_formats = override.formats
                
        # Merge Metadata Requirements
        final_metadata = dict(base.metadata_requirements)
        for k, v in override.metadata_requirements.items():
            if k in final_metadata and final_metadata[k] != v:
                raise OutputContractConflict(f"metadata_requirements.{k}", str(final_metadata[k]), str(v))
            final_metadata[k] = v
            
        # Merge Content Requirements
        final_content = list(base.content_requirements)
        for c in override.content_requirements:
            if c not in final_content:
                final_content.append(c)
                
        # Return new merged contract
        return OutputContract(
            output_contract_id=f"{base.output_contract_id}_merged",
            name=f"{base.name} (Merged)",
            display_name=base.display_name,
            output_type=base.output_type,
            cardinality=override.cardinality if override.cardinality != base.cardinality else base.cardinality,
            formats=final_formats,
            schema_reference=override.schema_reference or base.schema_reference,
            artifact_policy=override.artifact_policy if override.artifact_policy != base.artifact_policy else base.artifact_policy,
            delivery_policy=override.delivery_policy if override.delivery_policy != base.delivery_policy else base.delivery_policy,
            user_visible=override.user_visible,
            is_final=override.is_final,
            metadata_requirements=final_metadata,
            content_requirements=final_content
        )
