# Position Model

The Position model is the aggregate root representing a seat within a Team.

```python
class Position(BaseModel):
    id: Optional[str]
    position_id: str
    team_id: str
    name: str
    display_name: str
    description: str
    purpose: str
    version: str
    status: PositionStatus
    position_type: PositionType
    seniority: Seniority
    criticality: Criticality
    
    # Requirements defined at the position level
    required_skills: List[PositionSkillRequirement]
    required_tools: List[PositionToolRequirement]
    required_knowledge: List[PositionKnowledgeRequirement]
    reasoning_requirements: List[PositionReasoningRequirement]
    
    # Pipeline & Operational Responsibilities
    pipeline_responsibilities: List[str] # pipeline_ids
    stage_responsibilities: List[str] # stage_definition_ids
    output_responsibilities: List[str] # output_contract_ids
    quality_responsibilities: List[str] # quality_gate_ids
    
    workforce: WorkforceRequirement
    metadata: Dict[str, Any]
```

## Key Properties
- **No Execution**: The model declares what is required, it does not execute work.
- **Reference Integrity**: Responsibilities are defined using String IDs (`pipeline_ids`, `skill_id`, etc.) that act as references to established Phase 1-9 registries.
