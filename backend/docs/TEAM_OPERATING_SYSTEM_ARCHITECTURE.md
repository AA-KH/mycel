# Team Operating System Architecture (TOS 0)

## 1. Why The Architecture is Being Reset
Mycel is evolving from a flat collection of generic AI agents into an **AI Company Operating System**. Historically, logic was entangled: agents hired themselves, executing code held domain logic, and employees were conflated with runtimes. Phase TOS 0 establishes strict boundaries so that the system can cleanly orchestrate complex, domain-specific AI teams without monolithic spaghetti code.

## 2. Organization Definition
**What it is:** The structural hierarchy of the company.
**Owns:** `Company`, `Department`, `Team`, `Position`, relationships, tenant boundaries.
**Answers:** "WHERE does this entity belong?"
**Forbidden:** Must NOT own LLM execution, reasoning logic, or artifact generation.

## 3. Workforce Definition
**What it is:** The catalogue of human/agent specialist capabilities.
**Owns:** `Employee`, identities, skills, capabilities, specializations, reasoning/tool references.
**Answers:** "WHO is available to perform work?"
**Forbidden:** Must NOT execute LLM calls or execute tools directly. An employee is an identity entity, NOT a runtime.

## 4. Team Definition
**What it is:** A first-class operating unit defining how a domain solves problems.
**Owns:** Team identity, common skills, team knowledge, and (in future phases) team pipelines, reasoning philosophies, and quality gates.
**Answers:** "HOW does this domain solve problems?"
**Forbidden:** Must NOT directly execute LLM calls or bind tightly to runtime logic. 

## 5. Employee Definition
**What it is:** The specialized workforce identity mapped to a specific role.
**Owns:** `employee_id`, name, position, team, skills/proficiency, reasoning profile reference.
**Answers:** "WHO is this specialist?"
**Forbidden:** Does NOT execute tasks, does NOT create artifacts, and does NOT invoke tools directly. It merely provides the capability context.

## 6. Agent Definition
**What it is:** The executable AI identity derived from an Employee for a specific task.
**Owns:** runtime-facing identity configuration, capability snapshot reference, role constraints.
**Answers:** "WHAT AI identity is executing this work?"
**Forbidden:** Must NOT own MongoDB repository logic, company structures, or global hiring logic.

## 7. Runtime Definition
**What it is:** The execution environment that runs an Agent.
**Owns:** execution lifecycle (`AgentRuntime`), execution state, tool/reasoning invocation loops, events, cancellations, timeouts.
**Answers:** "HOW is this agent currently executing?"
**Forbidden:** Does NOT hire employees. Does NOT define team missions or employee identities.

## 8. Reasoning Definition
**What it is:** The strategy/methodology used by an Agent to approach a task.
**Owns:** Reasoning profiles (`research_verify`, `code_test`), task breakdown logic, observation integration.
**Answers:** "HOW should this agent approach the work?"
**Forbidden:** Must NOT select/create employees, store artifacts, or execute tools directly.

## 9. Tool Definition
**What it is:** The executable capabilities granted to the system.
**Owns:** Tool registries, tool execution gateways, tool permissions, schemas.
**Answers:** "WHAT actions can the agent perform?"
**Forbidden:** Must NOT decide which employee is hired or what an artifact semantically means.

## 10. Artifact Definition
**What it is:** Validated deliverables produced by the system.
**Owns:** Artifact identity, validation, references, storage abstraction (Cloudinary).
**Answers:** "WHAT was actually produced?"
**Forbidden:** Must NOT dictate reasoning logic, employee selection, or team pipelines.

## 11. Dependency Direction
Dependencies must flow strictly inwards or downwards to avoid cyclic or tangled domains. 
**Preferred Flow:**
`Organization -> Workforce -> Agent Definition -> Runtime -> Reasoning -> Tools -> Artifacts`

## 12. Identity Rules
Every major entity uses a stable, canonical UUID/string identifier. Display names are NEVER primary keys.
*   Company: `company_id`
*   Team: `team_id`
*   Position: `position_id`
*   Employee: `employee_id`
*   Agent: `agent_id`
*   Execution: `execution_id`
*   Tool: `tool_id`
*   Artifact: `artifact_id`

## 13. Context Rules
Execution context (`ExecutionContext`) must reference identities (IDs) rather than embedding entire domain objects (like full `Employee` objects). 

## 14. Snapshot Rules
When execution begins, a runtime-safe snapshot (`ExecutionSnapshot`) must be derived from the Employee. The runtime NEVER mutates or queries the live `Employee` database document during execution loops to guarantee consistency.

## 15. Persistence Boundaries
Repositories (`EmployeeRepository`, `ArtifactRepository`) own persistence. Application services and business logic MUST NOT contain raw MongoDB or driver-specific queries. 

## 16. Event Boundaries
Events must represent concrete domain state transitions (e.g., `agent.execution.started`, `artifact.created`). Arbitrary cross-domain events are forbidden.

## 17. API Boundaries
FastAPI routers must call application services. Routers must NEVER interact directly with Repositories (e.g. `Router -> Service -> Repository`).

## 18. Forbidden Dependencies
1.  Employee calling Groq directly.
2.  Employee executing tools directly.
3.  Agent selecting its own employee.
4.  Runtime selecting which employee should work.
5.  Tool deciding which employee should execute.
6.  Artifact deciding how an agent reasons.
7.  Hiring logic existing inside Runtime.
8.  Tool permission logic scattered across Employees instead of executed by ToolGateway.

## 19. Migration Strategy
Legacy components (`team_agents.py`, `legacy_adapter.py`, `manager_agent.py`) are flagged as `DEPRECATED`. They are preserved to ensure system stability while newer bounded domains (e.g., `HiringEngine`, `AgentRuntime`) are introduced alongside them. They will be progressively replaced by the Team Pipeline architecture.

## 20. Future Team Operating System Roadmap
*   **TOS 1:** Team Identity System
*   **TOS 2:** Team Knowledge & Skills
*   **TOS 3:** Team Pipelines & Output Contracts
