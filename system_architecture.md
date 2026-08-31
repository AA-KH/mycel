# Mycel: System Architecture (Current State)

This document outlines the system architecture of **Mycel (agent-virtual-office)** based on everything we have built up to this point. 

Mycel is a full-stack "Agent Operating System" where multiple AI agents collaborate to execute complex workflows, visualized in real-time within a pixel-art virtual office.

---

## 🏗️ High-Level Architecture

The system is divided into two primary layers: a **React Frontend** for visualization/control, and a **Python FastAPI Backend** for agent orchestration.

```mermaid
graph TD
    User([User]) --> |Task Input / Config| Frontend[React Frontend (Vite)]
    Frontend <--> |HTTP REST / WebSockets| Backend[FastAPI Backend]
    
    subgraph "Backend Orchestration"
        Backend --> Orchestrator[RabbitMQ / Event Bus]
        Orchestrator --> ManagerAgent[Manager Agent]
        ManagerAgent --> |Delegates| WorkerAgents[Specialized Team Agents (42 Roles)]
    end
    
    subgraph "External Integrations"
        WorkerAgents <--> |LLM Inference| Groq[Groq API (Primary & Fallback)]
        ManagerAgent <--> |LLM Inference| Groq
        Backend <--> |Intent Verification| ArmorIQ[ArmorIQ SDK]
    end
    
    subgraph "Frontend Engine"
        Frontend --> CanvasEngine[HTML5 Canvas Pixel Engine]
        Backend -.-> |Real-time Status Updates| CanvasEngine
    end
```

---

## 🖥️ Frontend (Visualization & Control)
**Stack:** React, Vite, TypeScript, Tailwind CSS

### Core Components:
1. **Virtual Office Engine (`CanvasOffice.tsx`)**
   - Renders a top-down, retro 21x22 tile pixel-art office using a 60fps HTML5 Canvas loop.
   - Handles agent sprites, pathfinding, and character state transitions (e.g., `WALK`, `IDLE`, `WORK`) based on real-time data.
2. **Dashboard & Config (`DashboardPage.tsx`)**
   - Manages Coder Host settings, MCP configurations, and API Keys.
3. **Task Panel (`TaskPanel.tsx`)**
   - UI for the human CEO to submit project prompts directly to the Manager Agent.
4. **Talent Market (`HireTalentModal.tsx`)**
   - Modal interface allowing the user to browse and dynamically spawn 42 distinct, specialized agent roles (e.g., `ui-designer`, `backend-architect`, `finance-tracker`).

---

## ⚙️ Backend (Agent Intelligence & Orchestration)
**Stack:** Python, FastAPI, RabbitMQ/NATS, Groq, WebSockets

### Core Components:
1. **Manager Agent (`manager_agent.py`)**
   - The central orchestrator. When a task is received, it queries Groq to create a structured JSON implementation plan.
   - Parses the plan and delegates subtasks sequentially to specialized agents.
2. **Team Agents (`team_agents.py`)**
   - Features a dynamic `GenericAgent` that assumes the identity of any of the 42 specialized roles assigned by the Manager.
   - Generates code, writes reports, and tests components based on the role's system prompt.
3. **Groq Failover Engine (`groq_engine.py`)**
   - Powers the intelligence with `llama-3.3-70b-versatile`.
   - Built-in resiliency that automatically routes traffic from `GROQ_API_KEY_1` to `GROQ_API_KEY_2` when rate limits (HTTP 429) are encountered.
4. **Real-time Event Broadcaster**
   - Uses WebSockets to continuously push agent lifecycle statuses (`working`, `idle`, `complete`, `failure`) directly to the frontend engine to drive the pixel sprites.

---

## 🔄 The Explore-Execute-Review (E²R) Lifecycle

When a task is submitted by the user, the following execution loop occurs:

1. **Submission:** User enters a prompt in the Task Panel.
2. **Routing:** FastAPI backend routes the prompt to the Manager Agent.
3. **Planning (Explore):** Manager Agent creates a multi-step JSON plan.
4. **Delegation:** Manager spawns the required roles (e.g., `ux-researcher`, `frontend-developer`).
5. **Execution:** Each specialized agent executes its subtask via Groq LLM inference.
6. **Visualization:** Throughout steps 3-5, the agents' pixel-art avatars move from their desks to "working" states on the frontend canvas.
7. **Synthesis (Review):** The Manager Agent collects all outputs, generates a final synthesized report, and logs the completion.

---

## 🔒 Security & Policies
- **ArmorIQ Integration:** Ensures task intents and agent actions are sanitized and verified before deep execution to prevent malicious prompts or unintended operations.

---

## 📁 Folder Structure

```text
mycel_final/
├── backend/                  # Python FastAPI Backend
│   ├── agents/               # AI Agent Logic
│   │   ├── base_agent.py     # Base class handling state and WebSocket emission
│   │   ├── manager_agent.py  # Orchestrator & E²R logic
│   │   └── team_agents.py    # 42 dynamic specialized roles + generic fallbacks
│   ├── core/                 # Core utilities (Groq engine, task logger, connections)
│   ├── modules/              # API endpoints (FastAPI routers)
│   ├── consumer_worker.py    # RabbitMQ background worker for processing tasks
│   ├── main.py               # FastAPI entry point
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Container configuration
│
├── frontend/                 # React + Vite Frontend
│   ├── src/
│   │   ├── components/       # React components (TaskPanel, HireTalentModal)
│   │   ├── config/           # Agent roles (agent-roles.ts mapped to 42 roles)
│   │   ├── hooks/            # Custom hooks for WebSockets, State
│   │   ├── pages/            # View views (DashboardPage, OfficePage)
│   │   └── pixel-office/     # HTML5 Canvas 2D engine ported for Mycel
│   ├── package.json          # Node dependencies
│   └── vite.config.ts        # Vite configuration
│
├── docker-compose.yaml       # Multi-container orchestration (API, Worker, RabbitMQ/Redis)
└── system_architecture.md    # This document
```
