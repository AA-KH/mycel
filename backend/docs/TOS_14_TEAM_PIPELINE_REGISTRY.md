# TOS 14: Team Pipeline Registry

The Team Pipeline Registry is the centralized discovery and access layer for all operational pipelines defined by Teams inside Mycel. It answers "What pipelines exist?" without crossing the boundary into execution.

## Architecture and Boundary

The `PipelineRegistry` acts strictly as a DIRECTORY.

**It is responsible for:**
- Knowing the canonical list of pipelines (`developer_development`, `research_discovery`, etc.).
- Enforcing strict 1:1 ownership between a Pipeline and a Team.
- Exposing the ordered sequence of `PipelineStage` objects required for execution.
- Exposing `input_contract` and `output_contract` references.

**It is explicitly restricted from:**
- Executing the pipeline.
- Executing the underlying tools, LLMs, or artifacts.
- Modifying Agent runtime states.

## Team Ownership Validation

Every pipeline is inextricably tied to a Team. During registration, the `PipelineRegistry` cross-references the `TeamRegistry` to ensure that the declared `team_id` is a valid, registered team. If a pipeline declares a team that doesn't exist (e.g., `invalid_team`), the registry throws a `PipelineRegistryError` and refuses registration.

## Discovery and Seeding

Pipelines are declared deterministically within their respective team's package (`teams/<team_id>/pipelines/<pipeline_id>.py`). 
The `PipelineCatalogue` scans these directories on application startup and registers them. It is highly resilient: a syntax error or validation failure in the Developer team's pipeline will not prevent the Research team's pipelines from being registered.

## Future Integrations

This discovery layer sets up the exact requirements for:
- **Task Routing:** "What pipeline does the creative team use for this?" -> The Task Router queries the pipeline registry for the Creative team's pipelines.
- **Pipeline Executor:** The executor will query the registry for `get_pipeline("creative_video_production")`, read the stages in exact order, and begin processing.
