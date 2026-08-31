# Target Mycel Architecture

The target architecture for the Mycel AI Company Operating System is designed to strictly separate agent identities (employees) from the orchestration, execution, and artifact verification runtimes. 

The monolithic `agents/` directory will be split into precise, specialized domains to support the long-term vision of unique, specialized AI employees operating within a dynamic corporate structure.

## Target Directory Structure & Responsibilities

### `backend/api/`
- **Responsibility**: External interfaces and routing.
- **Details**: Houses the FastAPI routers, HTTP endpoints, WebSocket connection managers, and authentication gateways. Handles all inbound and outbound client communication.

### `backend/company/`
- **Responsibility**: Organization definition.
- **Details**: Manages the structural definitions of Teams, Positions, and Department hierarchies. It does not contain execution logic, only the metadata describing the company layout.

### `backend/agents/`
- **Responsibility**: Employee Identity and Definitions.
- **Details**: Defines the unique "Employees" (e.g., Aarav Mehta, Riya Sharma), their reasoning profiles, skills, and base configurations. This is a registry of identities, NOT the runtime execution engine.

### `backend/hiring/`
- **Responsibility**: Talent acquisition and matching.
- **Details**: A smart system that takes a user task, extracts capability requirements, and calculates the best match from the Employee pool based on skills, reasoning quality, and past performance.

### `backend/orchestration/`
- **Responsibility**: Workflow and task management.
- **Details**: Replaces the legacy `ManagerAgent`. Decomposes complex projects into TaskNodes, manages dependencies between tasks, assigns them to Employees (via the Hiring system), and routes them to the Execution layer.

### `backend/tools/`
- **Responsibility**: Tool definitions and registry.
- **Details**: A centralized registry defining what a tool is (input/output schema), its permissions, and risk level. Employees request tools from this registry.

### `backend/artifacts/`
- **Responsibility**: Physical output validation and storage.
- **Details**: A critical subsystem ensuring that a task is only marked complete if the physical deliverable (video, code, PDF) exists, passes validation, is uploaded to storage (e.g., Cloudinary), and is registered for user delivery.

### `backend/execution/`
- **Responsibility**: The Agent Runtime.
- **Details**: The secure sandbox where an Employee Definition meets a Task. Handles the actual LLM inference loops (Understand -> Plan -> Execute -> Validate) using the Employee's assigned Reasoning Profile and authorized Tools.

### `backend/memory/`
- **Responsibility**: Persistence and state.
- **Details**: Manages short-term (contextual) and long-term (vectorized) memory for employees. Allows employees to recall past task interactions or company knowledge.

### `backend/communication/`
- **Responsibility**: Internal event bus and messaging.
- **Details**: Handles normalized events (`task.created`, `agent.working`, `artifact.delivered`) passing between subsystems and ultimately broadcasting to RabbitMQ or WebSockets.

### `backend/evaluation/`
- **Responsibility**: Output critique and quality assurance.
- **Details**: Dedicated automated judges or mechanisms that grade an Employee's reasoning and artifact quality *before* it is delivered to the user.

### `backend/upskill/`
- **Responsibility**: Employee progression.
- **Details**: Logic that updates an Employee's skill levels based on successful evaluations over time.

### `backend/infrastructure/`
- **Responsibility**: Core connections.
- **Details**: Contains database drivers (MongoDB), message brokers (RabbitMQ), LLM clients (Groq), and base configuration logic.

### `backend/workers/`
- **Responsibility**: Background processing.
- **Details**: Daemons that listen to RabbitMQ queues to trigger asynchronous processes (e.g., long-running artifact generation or async evaluations) outside the main HTTP thread.
