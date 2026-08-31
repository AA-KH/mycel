# Reasoning Engine Architecture

The Mycel Reasoning Engine is an advanced orchestration layer that bridges the gap between raw LLM generation and deterministic system execution. 

## Separation of Concerns

- **Agent Runtime**: Handles the actual execution of tools, memory lookup, artifact registration, and state persistence.
- **Reasoning Engine**: Responsible solely for *decision making*. It reads the context, applies a specialized reasoning strategy, and determines what the Runtime should do next (e.g., execute a specific tool or return a final answer).

## Core Concepts

### TaskIntent
When a task starts, the Reasoning Engine first normalizes it into a `TaskIntent`. This structured object clearly defines the goal, output type, constraints, and dependencies before any action is taken.

### Plan & PlanNode
The Engine generates a structured execution `Plan` consisting of `PlanNode` elements. This acts as a directed acyclic graph (DAG) of dependencies, ensuring the agent doesn't get lost in complex tasks.

### Context & Compression
`ReasoningContext` stores the active state of the current session, including `Observations` (tool results) and `Critiques`. To prevent the LLM context window from blowing up, older observations are dynamically compressed into summaries.

### Reasoning State Machine
1. `INITIALIZING`: Normalizing task into intent.
2. `PLANNING`: Decomposing intent into a plan.
3. `READY` / `EXECUTING`: Deciding the next action.
4. `OBSERVING`: Registering tool results.
5. `CRITIQUING`: Evaluating progress against the plan.
6. `REVISING`: Updating the plan if blocked.
7. `VERIFYING`: Checking final output against success criteria.
8. `COMPLETED` / `FAILED` / `BLOCKED`: Terminal states.
