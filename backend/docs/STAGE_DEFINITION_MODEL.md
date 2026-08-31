# Stage Definition Model

## Identity
Each `StageDefinition` utilizes a stable `stage_definition_id` (e.g., `web_research`, `video_generation`). It does not rely on display names.

## Versioning & Lifecycle
A `StageDefinition` maintains a `version` string and a `status` (`DRAFT`, `ACTIVE`, `DEPRECATED`, `ARCHIVED`). 
When a pipeline activates, the `PipelineStage` binds to a specific version. This prevents active pipelines from unexpectedly adopting new behaviors if a StageDefinition is modified in the future.

## Contracts
The core of a StageDefinition is comprised of logical contracts:
1. **Input Contract**: Defines exactly what physical inputs or logical descriptors are expected to commence the stage.
2. **Requirement Contract**: Declares the required Skills, Tools, Knowledge, and Reasoning logic necessary for success (For future Smart Hiring).
3. **Validation Contract**: Asserts specific criteria that must be met to mark the stage complete (e.g., specific artifacts generated).

## Reuse
A StageDefinition acts as a universal building block. `source_verification` is configured once but can be utilized by the Research Team Pipeline, the Legal Team Pipeline, and the Marketing Team Pipeline simultaneously.
