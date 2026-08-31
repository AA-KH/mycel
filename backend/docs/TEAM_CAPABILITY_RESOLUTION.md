# Team Capability Resolution Flow

The resolution flow defines how the `TeamCapabilityResolver` gathers disparate definitions across Mycel to formulate the `TeamCapabilityProfile`.

## System Relationships
1. **TeamRegistry (TOS 13):** The resolver begins here. It validates the Team exists and retrieves direct accessor data: `common_skills`, `common_tools`, `knowledge`, `reasoning`, and `positions`.
2. **PipelineRegistry (TOS 14):** The resolver delegates pipeline discovery to this registry. By passing the `team_id`, it acquires all pipelines definitively owned by the team.
3. **Pipeline Parsing:** The resolver recursively iterates over the retrieved `TeamPipeline` objects, extracting their defined `stages`, `output_contract_id`s, and `pipeline_gate_ids` (Quality constraints).

## CapabilityResolver (TOS 12) vs TeamCapabilityResolver (TOS 15)
- **TOS 12 (`CapabilityResolver`):** Focused on *vertical inheritance* (Company -> Department -> Team -> Position -> Baseline -> Member).
- **TOS 15 (`TeamCapabilityResolver`):** Focused on *horizontal integration*. It answers what the Team represents as a unified operational unit before vertical execution overrides occur. 

## The Task Routing Primitive
The flow culminates in `matches_requirements(team_id, requirements)`. This primitive acts as the ultimate gatekeeper for the future Task Router. If a task requires the output `video`, the resolver can authoritatively state if the Creative team has the capability to produce it.
