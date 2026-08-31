from typing import Dict, Set
from core.errors import DomainError
from .models import TeamPipeline

class PipelineValidator:
    """
    Validates the structural integrity of a TeamPipeline.
    Does NOT execute the pipeline.
    """
    
    @classmethod
    async def validate_graph(cls, pipeline: TeamPipeline, definition_registry=None):
        """
        Validates:
        1. All stage IDs are unique.
        2. All `depends_on` references point to existing stages.
        3. The dependency graph has no cycles (Acyclic).
        4. If definition_registry is provided, verifies `stage_definition_id` exists and is ACTIVE.
        """
        if not pipeline.input_contract.input_type:
            raise DomainError("Pipeline requires an 'input_type' in input_contract.")
            
        if not pipeline.output_contract_id:
            raise DomainError("Pipeline requires an output_contract_id.")
            
        stage_ids: Set[str] = set()
        
        # 1. Unique Stage IDs
        for stage in pipeline.stages:
            if stage.stage_id in stage_ids:
                raise DomainError(f"Duplicate stage ID found in pipeline '{pipeline.pipeline_id}': {stage.stage_id}")
            stage_ids.add(stage.stage_id)
            
            # 4. Definition Integrity
            if definition_registry:
                definition = await definition_registry.get_definition(stage.stage_definition_id, stage.stage_definition_version)
                if not definition:
                    raise DomainError(f"Stage '{stage.stage_id}' references unknown StageDefinition '{stage.stage_definition_id}' version '{stage.stage_definition_version}'")
                if definition.status != "active":
                    raise DomainError(f"Stage '{stage.stage_id}' references inactive StageDefinition '{stage.stage_definition_id}'")

            
        # 2. Dependency Validity & 3. Cycle Detection
        adj_list: Dict[str, List[str]] = {}
        for stage in pipeline.stages:
            for dep in stage.depends_on:
                if dep not in stage_ids:
                    raise DomainError(f"Stage '{stage.stage_id}' depends on non-existent stage '{dep}'")
            adj_list[stage.stage_id] = stage.depends_on
            
        cls._detect_cycles(adj_list)
        
    @classmethod
    def _detect_cycles(cls, adj_list: Dict[str, list[str]]):
        visited = set()
        rec_stack = set()
        
        def visit(node: str):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in adj_list.get(node, []):
                if neighbor not in visited:
                    visit(neighbor)
                elif neighbor in rec_stack:
                    raise DomainError(f"Cycle detected in pipeline graph involving stage '{neighbor}'")
                    
            rec_stack.remove(node)
            
        for node in adj_list.keys():
            if node not in visited:
                visit(node)
