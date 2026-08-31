# Phase TOS 10: Team Positions

## What is a Position?
A **Position** in the Mycel architecture defines a structured requirement for a specific type of worker inside a Team. It acts as a contract outlining exactly "What type of capability does this Team need?"
A Position specifies mandatory and preferred skills, tools, knowledge, reasoning philosophies, and outlines pipeline, stage, output, and quality responsibilities.

## Why is Position separate from Member?
- **Position** defines the *requirement* (e.g. The Backend Engineer must know Python and FastAPI).
- **Team Member** defines the *actual identity* of who currently occupies the role (e.g. Employee Kabir Sharma).
- If Kabir leaves the team, the `Backend Engineer` Position remains intact, clearly defining what the new hire must fulfill. Mixing these concepts would permanently fuse team structure with individual employee lifecycles, breaking future automated staffing (Smart Hiring).

## Position Lifecycle
Positions follow a strict lifecycle managed through `PositionStatus`:
- `DRAFT`: The Position is being defined.
- `ACTIVE`: The Position is currently valid and active for the Team.
- `INACTIVE`: Temporarily suspended from operation.
- `DEPRECATED`: Slated for removal; no new hires should be mapped here.
- `ARCHIVED`: Retained for historical auditing only.

## Position Requirements
A Position declares capabilities needed for success:
- **Required Skills:** Inherits Team Common skills and specifies required minimum proficiency levels for Position-specific skills.
- **Preferred Skills:** Identifies optional "nice-to-have" skills useful for Smart Hiring ranking.
- **Required Tools:** Software or integrations the Position must operate.
- **Knowledge & Reasoning:** Domain-specific RAG/search domains and reasoning profiles tailored for this role.

## Team Inheritance & Capabilities
Every Position implicitly inherits the `Common Skills`, `Common Tools`, and `Knowledge` established at the Team level.
A Position can **add** new requirements or **tighten** existing Team requirements (e.g., increasing minimum proficiency), but it **cannot weaken** mandatory Team capabilities.

## Position Responsibilities
Beyond skills, the Position declarative model includes:
- **Pipeline Responsibilities:** Which team pipelines the position participates in.
- **Stage Responsibilities:** Which execution stages the position is authorized to execute.
- **Output Responsibilities:** Which output contracts the position is responsible for delivering.

## Position to Member Relationship
A Team Member (`teams/<team_id>/team_members/emp_<id>/profile.py`) specifies a `position_id`. Upon runtime instantiation, the system looks up the Position definition to resolve the expected boundaries and capabilities of the Member.

## Position to Agent Relationship
The Position has zero execution capability. It does not spawn Agents, it does not call LLMs, and it does not use Tools.
The flow is strictly: **Position** -> defines -> **Member** -> maps to -> **Agent** -> runs on -> **Runtime**.

## Future Smart Hiring Relationship
By firmly decoupling the Position (requirements) from the Employee (capabilities), TOS 10 establishes the foundation for Phase TOS 11 (Smart Hiring). In the future, the hiring engine will match an open Position against the global Employee Catalogue by evaluating the delta between Position Requirements and Employee Skill Proficiencies.
