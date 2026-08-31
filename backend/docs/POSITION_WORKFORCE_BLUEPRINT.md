# Position Workforce Blueprint

A Position serves as a Workforce Blueprint. It defines the constraints and requirements for the headcount but does not act as a hiring manager.

## Workforce Requirement Schema
```python
class WorkforceRequirement(BaseModel):
    min_occupants: int = 0
    max_occupants: Optional[int] = None
    recommended_headcount: int = 1
    requiredness: Requiredness = Requiredness.REQUIRED
```

## Constraints
- **Separation of Duties**: Positions declare headcount needs. `Employees` and `Agents` fill these needs in a separate domain mapping logic.
- **No Agent Creation**: Resolving a blueprint does NOT spawn agents or hire employees. That logic belongs in Phase 11.
