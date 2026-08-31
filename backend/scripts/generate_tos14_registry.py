import os
from pathlib import Path

BACKEND_DIR = Path("d:/Projects/agent-virtual-office/backend")
TEAMS_DIR = BACKEND_DIR / "teams"
PIPELINES_DIR = BACKEND_DIR / "execution" / "pipelines"

PIPELINES = [
    ("developer", "development", "Development Pipeline", [
        ("research", 1), ("architecture", 2), ("development", 3), ("testing", 4), ("review", 5)
    ]),
    ("research", "discovery", "Discovery Pipeline", [
        ("discover", 1), ("collect", 2), ("verify", 3), ("synthesize", 4), ("review", 5)
    ]),
    ("creative", "video_production", "Video Production Pipeline", [
        ("concept", 1), ("scripting", 2), ("production", 3), ("editing", 4), ("quality", 5), ("delivery", 6)
    ]),
    ("legal", "legal_research", "Legal Research Pipeline", [
        ("legal_research", 1), ("authority_verification", 2), ("analysis", 3), ("drafting", 4), ("review", 5)
    ])
]

PIPELINE_TEMPLATE = """from execution.pipelines.models import TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="{team_id}_{pipeline_id}",
    team_id="{team_id}",
    name="{pipeline_id}",
    display_name="{display_name}",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(input_type="standard_task"),
    stages=[
{stages}
    ]
)
"""

STAGE_TEMPLATE = """        PipelineStage(
            stage_id="{stage_id}",
            name="{stage_id}",
            display_name="{stage_name}",
            order={order},
            stage_definition_id="{stage_id}_def"
        )"""

def generate_pipelines():
    for team_id, pipeline_id, display_name, stages_list in PIPELINES:
        pipeline_dir = TEAMS_DIR / team_id / "pipelines"
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        init_file = pipeline_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")
            
        stages_code = ",\n".join(
            STAGE_TEMPLATE.format(stage_id=s[0], stage_name=s[0].replace("_", " ").title(), order=s[1])
            for s in stages_list
        )
        
        content = PIPELINE_TEMPLATE.format(
            team_id=team_id, 
            pipeline_id=pipeline_id, 
            display_name=display_name, 
            stages=stages_code
        )
        (pipeline_dir / f"{pipeline_id}.py").write_text(content, encoding="utf-8")


REGISTRY_CONTENT = """import importlib
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
    \"\"\"Idempotent loader to discover pipelines from the filesystem.\"\"\"
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
"""

def generate_registry():
    PIPELINES_DIR.mkdir(parents=True, exist_ok=True)
    init_file = PIPELINES_DIR / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")
    
    registry_file = PIPELINES_DIR / "registry.py"
    registry_file.write_text(REGISTRY_CONTENT, encoding="utf-8")

if __name__ == "__main__":
    generate_pipelines()
    generate_registry()
    print("Generated TOS 14 Pipelines and Registry.")
