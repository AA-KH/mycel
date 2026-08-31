# Task Plan Schema Reference

## Task
- `task_id`: str (e.g. `task_a1b2c3d4`)
- `organization_id`: str
- `title`: str
- `description`: str
- `original_request`: str
- `normalized_request`: str
- `status`: TaskStatus (`CREATED`, `ANALYZING`, `PLANNING`, `PLAN_READY`, `WAITING_FOR_INPUT`, `BLOCKED`, `READY_FOR_EXECUTION`, etc.)
- `priority`: TaskPriority (`LOW`, `NORMAL`, `HIGH`, `URGENT`)
- `requested_outputs`: List[str]
- `constraints`: TaskConstraints
- `context`: TaskContext
- `current_plan_id`: Optional[str]

## WorkUnit
- `work_unit_id`: str (e.g. `wu_task_001`)
- `task_id`: str
- `team_id`: str
- `title`: str
- `objective`: str
- `inputs`: List[str]
- `required_capabilities`: List[str]
- `pipeline_id`: Optional[str]
- `execution_contract_id`: Optional[str]
- `collaboration_contract_id`: Optional[str]
- `expected_outputs`: List[str]
- `quality_requirements`: List[str]
- `required_position`: Optional[str]
- `dependencies`: List[str]
- `parallelizable`: bool

## WorkUnitDependency
- `dependency_id`: str
- `task_id`: str
- `from_work_unit_id`: str
- `to_work_unit_id`: str
- `dependency_type`: DependencyType (`OUTPUT_REQUIRED`, `ARTIFACT_REQUIRED`, `APPROVAL_REQUIRED`, `QUALITY_REQUIRED`, `CONTRACT_REQUIRED`)
- `required`: bool

## TaskPlan
- `plan_id`: str (e.g. `plan_task_v1`)
- `task_id`: str
- `version`: int
- `status`: TaskPlanStatus (`DRAFT`, `VALIDATING`, `READY`, `SUPERSEDED`, `CANCELLED`, `INVALID`)
- `objective`: str
- `work_units`: List[WorkUnit]
- `dependencies`: List[WorkUnitDependency]
- `expected_outputs`: List[str]
- `completion_criteria`: List[str]
- `failure_conditions`: List[str]
- `blockers`: List[PlanBlocker]
- `warnings`: List[PlanWarning]
