# Team Pipeline Registry Contract

The `PipelineRegistry` exposes a strict interface for retrieving information about pipelines.

## Discovery Methods
- `register(pipeline: TeamPipeline)`: Register a valid pipeline. Rejects duplicates and invalid team ownership.
- `unregister(pipeline_id: str)`: Remove a pipeline by ID.
- `exists(pipeline_id: str) -> bool`: Check if a pipeline is available.
- `list_pipelines() -> List[TeamPipeline]`: Returns all registered pipelines.
- `list_active() -> List[TeamPipeline]`: Returns pipelines with `PipelineStatus.ACTIVE`.
- `get_team_pipelines(team_id: str) -> List[TeamPipeline]`: Returns all pipelines owned by a specific team.

## Retrieval Methods
- `get_pipeline(pipeline_id: str) -> Optional[TeamPipeline]`: Retrieves the core operational pipeline model.
- `get_summary(pipeline_id: str) -> Dict[str, Any]`: Returns a flat dictionary with identity data and statistical counts (stage count, etc).
- `get_details(pipeline_id: str) -> Dict[str, Any]`: Returns a structured view including the actual stages, input/output contracts, and quality gate references.

*Note: The registry returns data representations. It does not provide execution context hooks.*
