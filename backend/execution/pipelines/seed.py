import asyncio
import logging
from core.mongodb import mongodb_connection
from organization.teams.repository import TeamRepository
from organization.registry import TeamRegistry

from execution.pipelines.repository import TeamPipelineRepository
from execution.pipelines.registry import TeamPipelineRegistry
from execution.pipelines.models import (
    TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus
)
from execution.stages.repository import StageDefinitionRepository
from execution.stages.registry import StageDefinitionRegistry
from execution.stages.catalogue import get_base_stage_definitions

logger = logging.getLogger(__name__)

async def seed_team_pipelines():
    """Idempotent seed for Stage Definitions and Team Pipelines."""
    logger.info("Starting Pipeline and Stage Definitions seed...")
    
    db = mongodb_connection.db
    
    team_repo = TeamRepository(db)
    team_registry = TeamRegistry(team_repo)
    
    definition_repo = StageDefinitionRepository(db)
    definition_registry = StageDefinitionRegistry(definition_repo)
    
    pipeline_repo = TeamPipelineRepository(db)
    pipeline_registry = TeamPipelineRegistry(pipeline_repo, team_registry)

    # 1. Seed Stage Definitions First
    definitions = get_base_stage_definitions()
    for definition in definitions:
        existing = await definition_registry.get_definition(definition.stage_definition_id, definition.version)
        if not existing:
            await definition_registry.register_definition(definition)
            logger.info(f"Registered StageDefinition: {definition.stage_definition_id}")
        else:
            logger.info(f"StageDefinition {definition.stage_definition_id} already exists.")

    # 2. Setup Backend Engineering Pipeline
    backend_team = await team_repo.get_by_id("team-backend")
    if backend_team:
        existing = await pipeline_registry.get_pipeline(backend_team.id, "engineering_pipeline")
        if not existing:
            stages = [
                PipelineStage(
                    stage_id="reqs",
                    name="understand_requirement",
                    display_name="Understand Requirement",
                    order=1,
                    stage_definition_id="understand_requirement",
                    depends_on=[]
                ),
                PipelineStage(
                    stage_id="impl",
                    name="implement",
                    display_name="Implement",
                    order=2,
                    stage_definition_id="code_implementation",
                    depends_on=["reqs"]
                ),
                PipelineStage(
                    stage_id="test",
                    name="test",
                    display_name="Test",
                    order=3,
                    stage_definition_id="test_execution",
                    depends_on=["impl"]
                )
            ]
            
            pipeline = TeamPipeline(
                pipeline_id="engineering_pipeline",
                team_id=backend_team.id,
                name="engineering_pipeline",
                display_name="Engineering Core Pipeline",
                status=PipelineStatus.ACTIVE,
                input_contract=PipelineInputContract(input_type="software_requirement"),
                output_contract_id="code_package",
                stages=stages
            )
            await pipeline_registry.create_pipeline(pipeline, definition_registry)
            logger.info(f"Created engineering_pipeline for {backend_team.id}")
        else:
            logger.info(f"engineering_pipeline already exists for {backend_team.id}")

    # 3. Setup Research Pipeline
    research_team = await team_repo.get_by_id("team-research")
    if research_team:
        existing = await pipeline_registry.get_pipeline(research_team.id, "research_pipeline")
        if not existing:
            stages = [
                PipelineStage(
                    stage_id="search",
                    name="search_sources",
                    display_name="Search Sources",
                    order=1,
                    stage_definition_id="web_research",
                    depends_on=[]
                ),
                PipelineStage(
                    stage_id="verify",
                    name="verify_evidence",
                    display_name="Verify Evidence",
                    order=2,
                    stage_definition_id="source_verification",
                    depends_on=["search"]
                ),
                PipelineStage(
                    stage_id="deliver",
                    name="deliver",
                    display_name="Deliver",
                    order=3,
                    stage_definition_id="research_synthesis",
                    depends_on=["verify"]
                )
            ]
            
            pipeline = TeamPipeline(
                pipeline_id="research_pipeline",
                team_id=research_team.id,
                name="research_pipeline",
                display_name="Research Pipeline",
                status=PipelineStatus.ACTIVE,
                input_contract=PipelineInputContract(input_type="task_description"),
                output_contract_id="research_report",
                stages=stages
            )
            await pipeline_registry.create_pipeline(pipeline, definition_registry)
            logger.info(f"Created research_pipeline for {research_team.id}")
        else:
            logger.info(f"research_pipeline already exists for {research_team.id}")

    logger.info("Team Pipeline seed complete.")

if __name__ == "__main__":
    asyncio.run(seed_team_pipelines())
