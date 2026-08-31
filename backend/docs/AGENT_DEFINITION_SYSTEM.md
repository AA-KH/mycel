# Agent Definition System (Phase 3)

## Overview

The Agent Definition System moves Mycel away from hardcoded generic roles (e.g., `GenericAgent("coder")`) toward a rich talent pool of **Unique AI Employees**.

An Employee defines **WHO** the agent is and **WHAT capabilities** they have. It does not dictate exactly **HOW** they are executed; that is the responsibility of the future Agent Runtime (Phase 4).

## Core Concepts

### Employee Identity
Each AI employee has a persistent identity. This includes their name, title, summary, personality, and communication style. This ensures that an employee (e.g., "Aarav Mehta") behaves consistently across multiple tasks.

### Skill Proficiency
Skills are stored as normalized values from `0-100` alongside their experience level. This structured data will power the future Smart Hiring system.

### Reasoning Profile
This determines the configuration for the future Reasoning Engine. It specifies:
- The strategy to use (e.g., `research_verify`, `plan_execute`).
- The required depth of planning.
- Whether validation/critique is mandatory.

### Tool Declarations and Permissions
Employees declare a list of tools they are trained to use (e.g., `browser.open`, `github.commit`). Independent of these declarations is a `Permissions` map which grants or denies authorization to use these tools in the company environment.

### Employee Registry
The `EmployeeRegistry` is the unified lookup service for all agents in the company. It will serve as the bridge between task requirements and the talent pool.

## Legacy Compatibility

Mycel still currently operates using `ManagerAgent` and `team_agents`.
To ensure no downtime for existing functionality, the legacy agents remain in place. We have introduced a `LegacyAgentAdapter` that will eventually serve to bridge legacy string roles to real registered employees as we migrate towards Phase 4 (Agent Runtime).
