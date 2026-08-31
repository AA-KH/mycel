# TOS 13: Team Registry

The Team Registry is the central discovery and access layer for operational Teams inside Mycel. It answers "What Teams exist?" without blurring the lines into operational orchestration.

## Architecture and Boundary

The `TeamRegistry` strictly acts as a DIRECTORY, not an ORCHESTRATOR. 

**It is responsible for:**
- Knowing the canonical list of Teams (`developer`, `research`, `creative`, etc.).
- Providing the base `Team` identity definitions.
- Providing pointers/references to Team common capabilities, positions, and members.
- Exposing lightweight metadata (status, descriptions).

**It is explicitly restricted from:**
- Resolving inherited capabilities (That is the domain of `CapabilityResolver` from TOS 12).
- Executing pipelines, tools, or agents.
- Performing Candidate matching (Smart Hiring).

## Discovery and Seeding

Teams are defined declaratively in the `teams/` directory structure. Each team folder contains a `team.py` file exposing an operational `Team` domain model instance.

The `TeamCatalogue` runs on application startup, scanning the `teams/` directory, validating identities, and registering them directly into the `TeamRegistry`. If one team is incorrectly configured, it is logged and skipped, ensuring the remainder of the registry remains functional (graceful degradation).

## Future Integrations

Because the Team Registry is a pure discovery layer, it acts as the primary entry point for future subsystems:
- **Task Routing:** "What Teams are available to handle this request?" -> Registry lists available active teams.
- **Smart Hiring:** "What does the Developer team require?" -> Registry points to the Positions and Baseline specifications.
