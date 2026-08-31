# Team Capability Model

The `TeamCapabilityProfile` represents a normalized, flat structure indicating exactly what operations, tools, and outputs a Team organizationally supports.

## Core Properties
1. **skills**: E.g., `programming`, `api_design`. Defines the functional proficiencies required.
2. **tools**: E.g., `github`, `terminal`. Defines the external applications/APIs the team utilizes.
3. **knowledge**: E.g., `engineering_standards`. Defines references to domain knowledge required.
4. **reasoning**: E.g., `engineering_reasoning`. Defines how the team mathematically or structurally approaches problem-solving.
5. **pipelines**: E.g., `development_pipeline`. Defines the overarching operational workflows owned.
6. **stages**: E.g., `code_review`. Granular capabilities mapped inside pipelines.
7. **outputs**: E.g., `source_code`. Defines the literal `output_contracts` the Team can generate.
8. **positions**: E.g., `backend_engineer`. Defines the roles present in the team.

## Explicit Non-Inference
Mycel firmly rejects "magic inference". 
- Just because a Team lists `github` as a tool does *not* mean the system infers they have the `deployment` capability. 
- Capabilities must be explicitly declared either natively on the Team definition or transitively through a Pipeline they explicitly own.
