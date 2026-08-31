# Phase 0 Architecture Audit

## Current Architecture
The `Mycel` backend is currently structured as a monolithic FastAPI application designed to orchestrate LLM-powered agents. It uses MongoDB for state and task logging, RabbitMQ for background event consumption, and WebSockets (via `manager`) to broadcast real-time status updates to a React frontend. The codebase relies heavily on the Groq API (with a built-in failover wrapper) for all inference.

## Current Request Flow
1. User submits a task via the frontend.
2. `POST /api/tasks/submit` route receives the request, logs it to MongoDB via `task_logger.py`, and immediately offloads the processing to an `asyncio.create_task` background coroutine.
3. The HTTP response is returned (202 Accepted) immediately.
4. The background coroutine orchestrates the `ManagerAgent`.

## Current Task Flow
1. **Planning**: `ManagerAgent` takes the user prompt, sends it to Groq, and receives a JSON breakdown of subtasks.
2. **Delegation**: The manager loops through the JSON subtasks and dynamically instantiates team agents (e.g., `CoderAgent`, `GenericAgent` via `build_team_agent`).
3. **Execution**: Each team agent executes its subtask sequentially via Groq and returns a text result.
4. **Synthesis**: The manager compiles all text results into a final Markdown report.
5. **Persistence**: All steps are sequentially written to MongoDB's `task_logs` collection.

## Current Agent Flow
- Agents inherit from `BaseAgent`.
- Agents do not have deep memory, tool permissions, or identity isolation. They are simply Python classes wrapping a `SYSTEM_PROMPT` and a `run_task()` method.
- Agents implicitly broadcast their own state (`working`, `idle`, `complete`) to the WebSockets during `run_task`.

## Current Realtime Flow
- A WebSocket manager handles active connections (`modules/realtime/`).
- Inside `BaseAgent.report_status()`, the agent creates a payload with its `session_id`, `role`, and `status`, updates the database, and then pushes an event directly to the WebSocket manager (`manager.broadcast(ws_data)`).
- This drives the pixel-art frontend visualization.

## Current Database Usage
- **MongoDB** is the primary datastore.
- `task_logger.py` handles writing task logs to the `task_logs` collection.
- `BaseAgent` handles writing agent session states to the `agent_sessions` collection.

## Current RabbitMQ Usage
- RabbitMQ connection (`core/rabbitmq.py`) is established on FastAPI startup.
- A separate `consumer_worker.py` script runs continuously, listening to RabbitMQ exchanges.
- Currently, it only seems to process an `auth0.webhook.received` event, indicating it handles external auth webhooks, but isn't heavily involved in the core agent task execution flow.

## Current Groq Usage
- Wrapped in `core/groq_engine.py` using `RobustGroqClient`.
- Implements an automatic failover between two API keys on HTTP 429 (Rate Limit) or quota errors.
- Default model used heavily is `llama-3.3-70b-versatile` (and `qwen/qwen3.6-27b` mapped in some hardcoded places).

## Existing Technical Debt
- Agents are tightly coupled to the WebSocket logic; they emit their own UI events.
- Hardcoded models in `run_task()` (e.g. `qwen/qwen3.6-27b`).
- Reasoning is embedded as a single prompt string, bypassing structured intermediate steps (Understand -> Decompose -> Plan).
- Tasks output raw markdown. There is no physical artifact delivery or verification pipeline.

## Existing Coupling
- `BaseAgent` is coupled to MongoDB and WebSockets.
- Orchestration is coupled to the `ManagerAgent` class rather than a discrete orchestration engine.

## Existing Reusable Components
- **`groq_engine.py`**: The failover logic is robust and reusable.
- **`mongodb.py` & `rabbitmq.py`**: Connection singletons.
- **`consumer_worker.py`**: Good foundation for background asynchronous execution.
- **FastAPI Core**: Standard layout, auth middleware, and routing structure.

## Files that should eventually be replaced
- `manager_agent.py` and `team_agents.py` (To be replaced by the dynamic Employee & Hiring system).
- `base_agent.py` (Must be split into Context, Reasoning, Tools, Execution).
- `task_logger.py` (To be replaced by a normalized Event contract system).

## Files that should remain
- `main.py`, `consumer_worker.py`, `core/config.py`, `core/mongodb.py`, `core/rabbitmq.py`, `core/groq_engine.py`.

## Files that should be moved
- Agent classes might move into `company/` or `execution/` domains according to the new architecture.

## Risks
- Decoupling the WebSockets from the Agents might break the frontend visualizer if not mapped correctly through an Event Bus.
- The new Employee Hiring logic might introduce high latency before a task even starts executing, compared to the current instant instantiation.

## Migration Strategy
1. Introduce the Domain Models without modifying current agents.
2. Build the `EventBus` and migrate `BaseAgent` to emit logical events (e.g. `agent.working`) rather than building WebSocket payloads directly.
3. Build the Artifact validation pipeline.
4. Replace `manager_agent.py` with the Orchestrator + Hiring System.
5. Deprecate legacy agents.
