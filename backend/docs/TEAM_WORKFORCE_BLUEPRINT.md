# Team Workforce Blueprint

This blueprint describes the structural relationship between structural definitions, human identities, and execution runtimes in the Mycel Team Operating System.

```mermaid
graph TD
    Org[Organization] --> Dept[Department]
    Dept --> Team[Team]
    
    Team --> Common[Common Capabilities]
    Common --> CS[Common Skills]
    Common --> CT[Common Tools]
    Common --> CK[Common Knowledge]
    Common --> CR[Reasoning Philosophy]

    Team --> Pipelines[Pipelines & Stages]
    
    Team --> Positions[Positions]
    Positions --> BE[Backend Engineer]
    Positions --> FE[Frontend Engineer]
    Positions --> QA[QA Engineer]
    
    Positions -.->|Defines Requirements for| Members
    
    Team --> Members[Team Members]
    Members --> M1[Kabir Sharma]
    
    M1 -.->|Occupies| BE
    M1 -.->|Brings| IS[Individual Specializations]
    
    Members --> Agent[Agent]
    Agent --> Runtime[Runtime Environment]
```

## Layers of Abstraction

1. **Team (The Domain):** Owns pipelines, quality gates, output contracts, and common standards.
2. **Position (The Requirement):** Belongs to the Team. Defines the exact responsibilities, skills, tools, and headcount needed for a specific seat in the Team.
3. **Team Member (The Assignment):** The actual workforce employee occupying the seat, bringing their unique identity, specializations, and personality.
4. **Agent (The Executor):** The LLM-driven entity that is spun up dynamically based on the Team Member's profile and the Position's capabilities.
5. **Runtime (The Environment):** The sandbox context managing lifecycle, state, timeouts, and boundaries for the Agent.
