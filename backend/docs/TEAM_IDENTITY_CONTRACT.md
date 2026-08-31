# Team Identity Contract

## Definition
The Team Identity Contract establishes the `team_id` as the anchor for all operational logic within Mycel.

## Core Rules
1. **Team Ownership**: Every Position must explicitly declare its `team_id`.
2. **Employee Assignment**: Employees (agents) are assigned to Positions, which binds them to a Team. An Employee must always have a `team_id` and `position_id`.
3. **Artifact Ownership**: All Artifacts must be owned by a `team_id`.
4. **Resolution**: The `TeamRegistry` (`organization/registry.py`) is the sole authority for validating and resolving Team identities across the system. No other domain should directly query the Team database collection.

## Structure
```json
{
  "id": "team-backend",
  "company_id": "mycel",
  "department_id": "dept-eng",
  "name": "Backend Engineering",
  "slug": "backend-engineering",
  "status": "active"
}
```
