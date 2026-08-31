from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import TeamPipeline, PipelineExecution

class TeamPipelineRepository(BaseRepository[TeamPipeline]):
    def __init__(self, db):
        super().__init__(db, "team_pipelines", TeamPipeline)

    async def get_by_pipeline_id(self, team_id: str, pipeline_id: str) -> Optional[TeamPipeline]:
        """Returns the specific active pipeline for a team by its stable ID."""
        docs = await self.find({"team_id": team_id, "pipeline_id": pipeline_id, "status": "active"}, limit=1)
        return docs[0] if docs else None
        
    async def get_all_active(self, team_id: str) -> List[TeamPipeline]:
        """Returns all active pipelines for a team."""
        return await self.find({"team_id": team_id, "status": "active"}, limit=100)

class PipelineExecutionRepository(BaseRepository[PipelineExecution]):
    def __init__(self, db):
        super().__init__(db, "pipeline_executions", PipelineExecution)

    async def get_by_execution_id(self, execution_id: str) -> Optional[PipelineExecution]:
        docs = await self.find({"execution_id": execution_id}, limit=1)
        return docs[0] if docs else None
