# The Employee Model

This document defines the canonical Employee structure for the Mycel architecture.

In Mycel, an **Employee** is a persistent, unique AI identity. We do not spawn "generic agents." We hire and execute unique talent.

## Critical Distinctions
- **Position != Employee**: A Position is a job description (e.g., "Senior Researcher"). An Employee is a unique identity holding that position (e.g., "Aarav Mehta").
- **Role != Employee Identity**: A role determines what an employee *does*, while identity determines *how* they do it (their personality, biases, and experience).
- **Agent Definition != Agent Runtime**: The Agent Definition is the static database record (the Employee JSON). The Agent Runtime is the Execution Engine that loads this definition to solve a task.
- **Skill != Tool**: "Video Editing" is a skill. "FFmpeg" is a tool. Skills are used by the hiring engine for matching; tools are executed during runtime.
- **Tool != Permission**: A tool exists in the global registry. A permission is a specific grant allowing an Employee to use that tool.

---

## Canonical Employee Schema

```json
{
    "id": "emp_01hqxyz9...",
    "name": "Aarav Mehta",
    "identity": "A meticulous, slightly pedantic data analyst who prefers rigorous, peer-reviewed sources and hates assumptions.",
    "team_id": "team_research_01",
    "position_id": "pos_sr_researcher",
    
    "personality": {
        "tone": "professional, dry, academic",
        "traits": ["thorough", "skeptical", "detail-oriented"]
    },
    
    "experience_level": "Senior",
    
    "skills": {
        "web_research": 96,
        "web_scraping": 94,
        "data_analysis": 91,
        "competitive_research": 89
    },
    
    "reasoning_profile": "research -> collect_evidence -> cross_validate -> synthesize -> cite",
    
    "tools": [
        "tool_web_search",
        "tool_browser",
        "tool_pdf_parser",
        "tool_citation_validator"
    ],
    
    "permissions": [
        {
            "tool_id": "tool_web_search",
            "allowed": true,
            "cost_limit": 5.00
        }
    ],
    
    "memory_config": {
        "vector_namespace": "aarav_mehta_longterm",
        "context_window_strategy": "summarize_oldest"
    },
    
    "performance": {
        "tasks_completed": 142,
        "average_evaluation_score": 9.4,
        "reliability_rating": 98.2
    },
    
    "version": "1.2.0",
    "status": "active"
}
```

## Field Definitions

| Field | Description |
|---|---|
| **`id`** | Unique identifier for the employee. |
| **`name`** | The display name / human identity of the employee. |
| **`identity`** | A core description of *who* this agent is, injected into the system prompt context. |
| **`team_id`** | Reference to the `Team` this employee belongs to. |
| **`position_id`** | Reference to the `Position` they fulfill. |
| **`personality`** | Granular traits affecting the output style and communication format. |
| **`experience_level`** | Junior, Mid, Senior, Lead. Impacts reasoning depth and tool permissions. |
| **`skills`** | A dictionary mapping domain capabilities to a proficiency score (0-100). |
| **`reasoning_profile`** | The specific lifecycle strategy the execution engine will run (e.g., standard CoT, ReAct, or domain-specific workflows). |
| **`tools`** | A list of Tool IDs the employee is aware of. |
| **`permissions`** | Explicit authorization grants and constraints (e.g., spending limits) for using tools. |
| **`memory_config`** | How this specific employee stores and retrieves context. |
| **`performance`** | Historical metadata updated automatically by the `Evaluation` subsystem. |
| **`version`** | Schema/iteration version of this employee's definition. |
| **`status`** | Active, suspended, or archived. |
