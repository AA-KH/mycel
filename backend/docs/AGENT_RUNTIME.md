# Agent Runtime (Phase 4)

The **Agent Runtime** is the universal execution engine for Mycel AI Employees.

## Abstraction Model

`Employee Definition -> Agent Runtime -> Execution Result`

The Agent Runtime does NOT care what the employee's role is (e.g., Researcher, Coder). It only executes the structured `ExecutionSnapshot` (built from the Employee Definition) against a given task.

## Key Components

1. **`ExecutionContext`** (`context.py`): The immutable context that flows through the system. It tracks the `execution_id`, `task_id`, `employee_id`, and organizational context.
2. **`RuntimeState`** (`state.py`): The state machine governing execution (CREATED -> INITIALIZING -> PLANNING -> EXECUTING -> WAITING_TOOL -> OBSERVING -> VERIFYING -> COMPLETED).
3. **`ExecutionSnapshot`** (`snapshot.py`): An immutable record of the Employee at the time of execution. Ensures changes to the employee definition don't disrupt running tasks.
4. **`InstructionBuilder`** (`instruction_builder.py`): Dynamically builds the system prompt from the `ExecutionSnapshot` instead of hardcoding roles.
5. **`AgentRuntime`** (`lifecycle.py`): The core orchestrator. Evaluates actions iteratively in a bounded loop until a final answer is reached or max iterations hit.
6. **`LLMProvider`** (`execution/llm/provider.py`): Abstraction layer for the underlying LLM (Groq). Enforces structured JSON output.
7. **`RuntimeEventPublisher`** (`events.py`): Emits state changes and persists the result to the MongoDB `agent_executions` collection.

## Execution Flow

1. Runtime is instantiated with injected dependencies (ToolGateway, Verifier, etc.).
2. `AgentRuntime.execute(snapshot, task, context)` is called.
3. System prompt is built via `InstructionBuilder`.
4. LLM loop begins (up to `max_tool_iterations`).
5. The LLM decides on an `action` (`tool_call` or `final_answer`).
6. If `tool_call`, permissions are checked, tool executed, and result fed back to the LLM.
7. If `final_answer`, the loop exits.
8. `ResultVerifier` verifies the final output.
9. Execution is marked `COMPLETED` (or `FAILED`) and metrics are persisted.

## Adapting Legacy Agents

The `AgentRuntimeAdapter` (in `legacy_adapter.py`) allows existing orchestration logic (`ManagerAgent`) to utilize the new Agent Runtime transparently. It maps a legacy `run_task` call into an `ExecutionSnapshot`, creates an `ExecutionContext`, and runs the `AgentRuntime` engine.
