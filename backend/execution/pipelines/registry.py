import importlib
import logging
from typing import Dict, List, Optional, Any
from execution.pipelines.models import TeamPipeline, PipelineStatus

logger = logging.getLogger(__name__)

class PipelineRegistryError(Exception):
    pass

class PipelineRegistry:
    def __init__(self, team_registry=None):
        self._pipelines: Dict[str, TeamPipeline] = {}
        self.team_registry = team_registry

    def register(self, pipeline: TeamPipeline) -> None:
        if not pipeline.pipeline_id:
            raise PipelineRegistryError("Pipeline must have a pipeline_id.")
        if pipeline.pipeline_id in self._pipelines:
            raise PipelineRegistryError(f"Pipeline {pipeline.pipeline_id} is already registered.")
            
        if not pipeline.team_id:
            raise PipelineRegistryError("Pipeline must declare a team_id.")
            
        if self.team_registry:
            if not self.team_registry.exists(pipeline.team_id):
                raise PipelineRegistryError(f"Team {pipeline.team_id} does not exist.")
        
        self._pipelines[pipeline.pipeline_id] = pipeline
        logger.info(f"Registered pipeline: {pipeline.pipeline_id} for team {pipeline.team_id}")

    def unregister(self, pipeline_id: str) -> None:
        if pipeline_id in self._pipelines:
            del self._pipelines[pipeline_id]

    def get_pipeline(self, pipeline_id: str) -> Optional[TeamPipeline]:
        return self._pipelines.get(pipeline_id)

    def exists(self, pipeline_id: str) -> bool:
        return pipeline_id in self._pipelines

    def list_pipelines(self) -> List[TeamPipeline]:
        return list(self._pipelines.values())

    def list_active(self) -> List[TeamPipeline]:
        return [p for p in self._pipelines.values() if p.status == PipelineStatus.ACTIVE]

    def get_team_pipelines(self, team_id: str) -> List[TeamPipeline]:
        return [p for p in self._pipelines.values() if p.team_id == team_id]

    def get_summary(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return None
        return {
            "pipeline_id": pipeline.pipeline_id,
            "team_id": pipeline.team_id,
            "display_name": pipeline.display_name,
            "status": pipeline.status,
            "version": pipeline.version,
            "stage_count": len(pipeline.stages),
            "output_type": pipeline.output_contract_id,
            "quality_gate_count": len(pipeline.pipeline_gate_ids)
        }

    def get_details(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return None
        return {
            "identity": pipeline.model_dump(exclude={"stages", "input_contract"}),
            "team": pipeline.team_id,
            "stages": [s.model_dump() for s in pipeline.stages],
            "input_contract": pipeline.input_contract.model_dump() if pipeline.input_contract else None,
            "output_contract": pipeline.output_contract_id,
            "quality_references": pipeline.pipeline_gate_ids,
            "metadata": pipeline.metadata
        }

class PipelineCatalogue:
    """Idempotent loader to discover pipelines from the filesystem."""
    def __init__(self, registry: PipelineRegistry):
        self.registry = registry

    def load_from_directory(self, base_dir: str):
        import os
        from pathlib import Path
        base_path = Path(base_dir)
        if not base_path.exists():
            return
            
        for team_dir in base_path.iterdir():
            if team_dir.is_dir():
                pipelines_dir = team_dir / "pipelines"
                if pipelines_dir.exists() and pipelines_dir.is_dir():
                    for pipe_file in pipelines_dir.glob("*.py"):
                        if pipe_file.name == "__init__.py":
                            continue
                            
                        try:
                            module_name = f"teams.{team_dir.name}.pipelines.{pipe_file.stem}"
                            spec = importlib.util.spec_from_file_location(module_name, str(pipe_file))
                            if spec and spec.loader:
                                module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(module)
                                if hasattr(module, "pipeline_instance"):
                                    # Basic verification that the folder matches the declared team
                                    inst = module.pipeline_instance
                                    if inst.team_id != team_dir.name:
                                        raise PipelineRegistryError(f"Pipeline {inst.pipeline_id} claims team {inst.team_id} but is in {team_dir.name}")
                                    self.registry.register(inst)
                        except PipelineRegistryError as e:
                            logger.error(f"Validation failed for {pipe_file.name}: {e}")
                        except Exception as e:
                            logger.error(f"Failed to load pipeline {pipe_file.name}: {e}")
